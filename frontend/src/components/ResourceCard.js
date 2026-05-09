'use client';
import styles from '@/app/page.module.css';

/**
 * ResourceCard
 *
 * Reusable card for displaying a single FHIR resource type.
 * Handles three states: loading (skeleton), empty (no data), and populated.
 *
 * Props:
 *   title       {string}   — display name e.g. "Conditions"
 *   code        {string}   — short badge code e.g. "CD"
 *   accent      {string}   — CSS variable for the accent color e.g. "var(--accent-red)"
 *   description {string}   — subtitle e.g. "Diagnoses & health problems"
 *   data        {any}      — raw FHIR resource or bundle from Epic (null while loading)
 *   loading     {boolean}  — true while parent is fetching data
 *   extract     {function} — (data) => [{ label, value }, ...] — resource-specific extractor
 */
export default function ResourceCard({ title, code, accent, description, data, loading, extract }) {
  const fields = loading ? [] : extract(data);
  const empty  = !loading && fields.length === 0;

  return (
    <div className={styles.card}>

      {/* Header */}
      <div className={styles.cardHeader}>
        <div className={styles.cardBadge} style={{ '--card-accent': accent }}>
          {code}
        </div>
        <div>
          <h2 className={styles.cardTitle}>{title}</h2>
          <p className={styles.cardDesc}>{description}</p>
        </div>
      </div>

      {/* Accent divider */}
      <div className={styles.cardDivider} style={{ '--card-accent': accent }} />

      {/* Body — three states */}
      {loading ? (
        <div className={styles.skeletonList}>
          {[...Array(5)].map((_, i) => (
            <div key={i} className={styles.skeletonRow} />
          ))}
        </div>
      ) : empty ? (
        <p className={styles.emptyState}>No data available</p>
      ) : (
        <ul className={styles.fieldList}>
          {fields.map((f, i) => (
            <li key={i} className={styles.fieldItem}>
              <span className={styles.fieldDot} style={{ '--card-accent': accent }} />
              <span className={styles.fieldName}>{f.label}</span>
              <span className={styles.fieldValue}>{f.value}</span>
            </li>
          ))}
        </ul>
      )}

      {/* Footer */}
      <div className={styles.cardFooter}>
        <span className={styles.fhirLabel}>FHIR/{title}</span>
        {!loading && (
          <span className={styles.recordCount}>
            {empty
              ? '0 records'
              : `${fields.length} record${fields.length !== 1 ? 's' : ''}`
            }
          </span>
        )}
      </div>

    </div>
  );
}