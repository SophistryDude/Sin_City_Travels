#!/usr/bin/env bash
set -euo pipefail

# ─── Sin City Travels — Database Backup Script ───────────────────────────────
#
# Dumps the PostgreSQL database to a compressed file.
# Intended to run daily via cron (installed by deploy.sh).
#
# Usage:
#   sudo /opt/sincitytravels/backup_db.sh
# ─────────────────────────────────────────────────────────────────────────────

BACKUP_DIR="/var/backups/sincitytravels"
LOG_FILE="/var/log/sincitytravels/backup.log"
DB_NAME="sincitytravels"
RETENTION_DAYS=7

mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "Starting backup..."

# Dump and compress
if sudo -u postgres pg_dump "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
    # Verify non-empty
    FILE_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}" 2>/dev/null)
    if [ "${FILE_SIZE}" -gt 100 ]; then
        log "Backup created: ${BACKUP_FILE} (${FILE_SIZE} bytes)"
    else
        log "ERROR: Backup file is suspiciously small (${FILE_SIZE} bytes)"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi
else
    log "ERROR: pg_dump failed"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Clean up old backups
DELETED=$(find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    log "Cleaned up ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi

log "Backup complete."
