-- Migration 007: Rename tables to raw_ prefix for DBT source models
-- This migration renames all core tables to follow the raw_ naming convention
-- Author: Database refactoring for DBT integration
-- Date: 2025-11-02

-- Rename core tables
ALTER TABLE IF EXISTS stocks RENAME TO raw_stocks;
ALTER TABLE IF EXISTS stock_prices RENAME TO raw_stock_prices;
ALTER TABLE IF EXISTS dividend_history RENAME TO raw_dividends;
ALTER TABLE IF EXISTS stock_splits RENAME TO raw_stock_splits;
ALTER TABLE IF EXISTS stock_prices_hourly RENAME TO raw_stock_prices_hourly;
ALTER TABLE IF EXISTS holdings_history RENAME TO raw_holdings_history;
ALTER TABLE IF EXISTS stocks_excluded RENAME TO raw_stocks_excluded;
ALTER TABLE IF EXISTS excluded_symbols RENAME TO raw_excluded_symbols;
ALTER TABLE IF EXISTS activity_history RENAME TO raw_activities;

-- Update all foreign key references and constraints
-- Note: PostgreSQL automatically updates foreign key references when renaming tables,
-- but we should verify constraint names are still meaningful

-- Verify indexes are preserved (they are automatically renamed by PostgreSQL)
-- Example: idx_stocks_symbol becomes idx_raw_stocks_symbol

-- Add comment to track migration
COMMENT ON TABLE raw_stocks IS 'Raw stock data - source for DBT models (renamed from stocks in migration 007)';
COMMENT ON TABLE raw_stock_prices IS 'Raw stock price data - source for DBT models (renamed from stock_prices in migration 007)';
COMMENT ON TABLE raw_dividends IS 'Raw dividend data - source for DBT models (renamed from dividend_history in migration 007)';
COMMENT ON TABLE raw_stock_splits IS 'Raw stock split data - source for DBT models (renamed from stock_splits in migration 007)';
COMMENT ON TABLE raw_stock_prices_hourly IS 'Raw hourly stock prices - source for DBT models (renamed from stock_prices_hourly in migration 007)';
COMMENT ON TABLE raw_holdings_history IS 'Raw holdings history - source for DBT models (renamed from holdings_history in migration 007)';
COMMENT ON TABLE raw_stocks_excluded IS 'Raw excluded stocks - source for DBT models (renamed from stocks_excluded in migration 007)';
COMMENT ON TABLE raw_excluded_symbols IS 'Raw excluded symbols list - source for DBT models (renamed from excluded_symbols in migration 007)';
COMMENT ON TABLE raw_activities IS 'Raw activity history - source for DBT models (renamed from activity_history in migration 007)';
