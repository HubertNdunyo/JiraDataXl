-- Migration: Add performance metrics table
-- Date: 2025-08-08
-- Purpose: Enable performance tracking for sync operations

-- Create sync_performance_metrics table
CREATE TABLE IF NOT EXISTS sync_performance_metrics (
    id SERIAL PRIMARY KEY,
    sync_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sync_id) REFERENCES sync_history(sync_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_sync_id 
ON sync_performance_metrics(sync_id);

CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_name 
ON sync_performance_metrics(metric_name);

CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_recorded 
ON sync_performance_metrics(recorded_at);

-- Add comment
COMMENT ON TABLE sync_performance_metrics IS 'Stores performance metrics for sync operations';