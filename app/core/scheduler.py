from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Instancia global del scheduler
scheduler = AsyncIOScheduler()

def start_scheduler():
    """Inicia el scheduler en el lifespan de la app"""
    # Ejemplo de tarea: Cada noche purgar logs antiguos o encolar tarea de ML
    # scheduler.add_job(mi_funcion, 'cron', hour=2, minute=0)
    scheduler.start()
    print("Scheduler started")

def shutdown_scheduler():
    """Apaga el scheduler al detener la app"""
    scheduler.shutdown()
    print("Scheduler shutdown")
