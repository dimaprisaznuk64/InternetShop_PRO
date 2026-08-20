-- InternetShop PRO — DB Performance Audit Queries
-- Run: psql -U postgres -d internetshop -f deploy/db-performance.sql

\echo '=== Index Usage ==='
SELECT
    schemaname,
    relname AS table_name,
    seq_scan,
    idx_scan,
    CASE WHEN seq_scan + COALESCE(idx_scan, 0) > 0
         THEN round(100.0 * COALESCE(idx_scan, 0) / (seq_scan + COALESCE(idx_scan, 0)), 1)
         ELSE 0 END AS idx_usage_pct,
    CASE WHEN seq_scan > 100 AND (idx_scan IS NULL OR idx_scan = 0)
         THEN 'NEEDS INDEX' ELSE 'ok' END AS status
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;

\echo ''
\echo '=== Unused Indexes ==='
SELECT
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan < 10
ORDER BY pg_relation_size(indexrelid) DESC;

\echo ''
\echo '=== Table Bloat (dead tuples) ==='
SELECT
    relname,
    n_live_tup,
    n_dead_tup,
    CASE WHEN n_live_tup > 0
         THEN round(100.0 * n_dead_tup / n_live_tup, 1)
         ELSE 0 END AS dead_pct,
    CASE WHEN n_live_tup > 0 AND n_dead_tup::float / n_live_tup > 0.2
         THEN 'NEEDS VACUUM' ELSE 'ok' END AS status
FROM pg_stat_user_tables
WHERE n_dead_tup > 100
ORDER BY n_dead_tup DESC;

\echo ''
\echo '=== Slow Queries (pg_stat_statements) ==='
SELECT
    query,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

\echo ''
\echo '=== Table Sizes ==='
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename::regclass)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;

\echo ''
\echo '=== Cache Hit Ratio ==='
SELECT
    round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read) + 1), 2) AS cache_hit_pct
FROM pg_stat_database
WHERE datname = current_database();

\echo ''
\echo '=== Connection Stats ==='
SELECT
    state,
    count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;

\echo ''
\echo '=== Long Running Queries ==='
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;
