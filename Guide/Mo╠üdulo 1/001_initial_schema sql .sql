-- GJS Recommendation Engine MVP - Initial Schema

CREATE TABLE customers (
  customer_id VARCHAR(50) PRIMARY KEY,
  business_type VARCHAR(100) NOT NULL,
  city VARCHAR(100) NOT NULL,
  average_order_value NUMERIC(14,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
  product_id VARCHAR(50) PRIMARY KEY,
  sku VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100) NOT NULL,
  margin_pct NUMERIC(6,4) NOT NULL,
  strategic_priority NUMERIC(6,4) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE purchases (
  purchase_id BIGSERIAL PRIMARY KEY,
  customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
  product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
  quantity NUMERIC(14,2) NOT NULL,
  purchased_at TIMESTAMP NOT NULL,
  channel VARCHAR(50),
  city VARCHAR(100)
);

CREATE TABLE affinity_rules (
  rule_id BIGSERIAL PRIMARY KEY,
  source_category VARCHAR(100) NOT NULL,
  target_category VARCHAR(100) NOT NULL,
  weight NUMERIC(6,4) NOT NULL,
  reason_code VARCHAR(100) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE recommendation_runs (
  run_id BIGSERIAL PRIMARY KEY,
  customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
  generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  channel VARCHAR(50),
  business_type VARCHAR(100),
  city VARCHAR(100)
);

CREATE TABLE recommendation_results (
  result_id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES recommendation_runs(run_id),
  product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
  score NUMERIC(8,4) NOT NULL,
  reason_codes JSONB NOT NULL
);
