import sys
import traceback
from rq import Worker, Queue
from app.core.queue import redis_conn
from app.db.session import engine
from sqlmodel import Session
from app.models.integration import FailedJobLog

# Lista de colas a escuchar
listen = ['default']

def process_webhook_event(provider: str, event_type: str, payload_str: str, integration_log_id: int):
    """
    Función que será encolada por el webhook para procesamiento pesado.
    Si falla, el Exception Handler de RQ lo capturará (o podemos manejarlo aquí).
    """
    print(f"Processing event {event_type} from {provider} (Log ID: {integration_log_id})")
    
    # Aquí iría toda la lógica de mapeo de IDs, actualización de inventario, etc.
    # Simulamos trabajo pesado
    import time
    time.sleep(1)
    
    # Actualizar estado a completado si quisiéramos
    from app.models.integration import IntegrationLog
    with Session(engine) as session:
        log_entry = session.get(IntegrationLog, integration_log_id)
        if log_entry:
            log_entry.status = "processed_async"
            session.add(log_entry)
            session.commit()
    print(f"Finished processing event {integration_log_id}")


def handle_failed_job(job, exc_type, exc_value, tb):
    """
    Manejador de fallos de RQ. Guarda el error en la Dead-Letter table.
    """
    error_msg = f"{exc_type.__name__}: {exc_value}"
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
    
    with Session(engine) as session:
        failed_log = FailedJobLog(
            job_id=job.id,
            queue_name=job.origin,
            payload=str(job.args) + str(job.kwargs),
            error_message=error_msg,
            traceback=tb_str
        )
        session.add(failed_log)
        session.commit()
        
    print(f"Job {job.id} failed and saved to Dead-Letter Queue.")


if __name__ == '__main__':
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(queues, exception_handlers=[handle_failed_job], connection=redis_conn)
    worker.work()
