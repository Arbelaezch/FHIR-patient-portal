'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApi, fhirApi } from '@/lib/fhirClient';
import ResourceCard from '@/components/ResourceCard';
import styles from './page.module.css';

// ---------------------------------------------------------------------------
// FHIR data extractors
// Each receives the raw Epic response and returns [{ label, value }, ...]
// Returns [] for null/empty input — ResourceCard renders "No data available"
// ---------------------------------------------------------------------------

function extractPatient(resource) {
  if (!resource) return [];
  const name = resource.name?.[0];
  const fullName = name
    ? [name.prefix?.join(' '), name.given?.join(' '), name.family].filter(Boolean).join(' ')
    : '—';

  // Epic uses various identifier type texts — grab the first available one
  const identifier = resource.identifier?.find(i =>
    ['MRN', 'EPIC', 'CEID'].includes(i.type?.text)
  );
  const mrn   = identifier?.value ?? '—';
  const phone = resource.telecom?.find(t => t.system === 'phone')?.value ?? '—';

  return [
    { label: 'Name',          value: fullName },
    { label: 'Date of Birth', value: resource.birthDate ?? '—' },
    { label: 'Gender',        value: resource.gender ?? '—' },
    { label: 'MRN',           value: mrn },
    { label: 'Contact',       value: phone },
  ];
}

function extractObservations(bundle) {
  if (!bundle?.entry?.length) return [];
  return bundle.entry.slice(0, 5).map(e => {
    const obs   = e.resource;
    const label = obs.code?.text ?? obs.code?.coding?.[0]?.display ?? 'Observation';
    const qty   = obs.valueQuantity;
    const value = qty
      ? `${qty.value} ${qty.unit ?? ''}`.trim()
      : obs.valueString ?? obs.valueCodeableConcept?.text ?? '—';
    return { label, value };
  });
}

function extractMedications(bundle) {
  if (!bundle?.entry?.length) return [];
  return bundle.entry.slice(0, 5).map(e => {
    const med   = e.resource;
    const label = med.medicationCodeableConcept?.text
               ?? med.medicationCodeableConcept?.coding?.[0]?.display
               ?? med.medicationReference?.display
               ?? 'Medication';
    const dosage = med.dosageInstruction?.[0];
    const value  = dosage?.text
               ?? (dosage?.doseAndRate?.[0]?.doseQuantity
                  ? `${dosage.doseAndRate[0].doseQuantity.value} ${dosage.doseAndRate[0].doseQuantity.unit ?? ''}`.trim()
                  : null)
               ?? med.status
               ?? '—';
    return { label, value };
  });
}

function extractConditions(bundle) {
  if (!bundle?.entry?.length) return [];
  return bundle.entry.slice(0, 5).map(e => {
    const cond  = e.resource;
    const label = cond.code?.text ?? cond.code?.coding?.[0]?.display ?? 'Condition';
    const value = cond.clinicalStatus?.coding?.[0]?.code ?? cond.verificationStatus?.coding?.[0]?.code ?? '—';
    return { label, value };
  });
}

// ---------------------------------------------------------------------------
// Resource card config
// ---------------------------------------------------------------------------

const RESOURCE_CONFIG = [
  {
    key:         'patient',
    title:       'Patient',
    code:        'PT',
    accent:      'var(--accent-blue)',
    description: 'Demographics & identifiers',
    extract:     extractPatient,
  },
  {
    key:         'observation',
    title:       'Observations',
    code:        'OB',
    accent:      'var(--accent-green)',
    description: 'Vitals, labs & clinical findings',
    extract:     extractObservations,
  },
  {
    key:         'medication',
    title:       'Medications',
    code:        'MR',
    accent:      'var(--accent-amber)',
    description: 'Active prescriptions & requests',
    extract:     extractMedications,
  },
  {
    key:         'condition',
    title:       'Conditions',
    code:        'CD',
    accent:      'var(--accent-red)',
    description: 'Diagnoses & health problems',
    extract:     extractConditions,
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const router = useRouter();

  const [session,  setSession]  = useState(null);
  const [fhirData, setFhirData] = useState({});
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);

  // Check session on mount
  useEffect(() => {
    authApi.getSession()
      .then(setSession)
      .catch(err => {
        if (err.status === 401) router.replace('/login');
        else setError('Could not reach the server.');
      });
  }, [router]);

  // Fetch all four FHIR resources in parallel once we have a patient ID
  useEffect(() => {
    if (!session?.patient_id) return;

    const { patient_id } = session;

    Promise.allSettled([
      fhirApi.getPatient(patient_id),
      fhirApi.getObservations(),
      fhirApi.getMedicationRequests(),
      fhirApi.getConditions(),
    ]).then(([patient, observations, medications, conditions]) => {
      setFhirData({
        patient:     patient.status      === 'fulfilled' ? patient.value      : null,
        observation: observations.status === 'fulfilled' ? observations.value : null,
        medication:  medications.status  === 'fulfilled' ? medications.value  : null,
        condition:   conditions.status   === 'fulfilled' ? conditions.value   : null,
      });
      setLoading(false);
    });
  }, [session]);

  const patientName = (() => {
    const name = fhirData.patient?.name?.[0];
    if (!name) return 'Patient';
    return [name.given?.join(' '), name.family].filter(Boolean).join(' ');
  })();

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 18) return 'Good afternoon';
    return 'Good evening';
  })();

  if (error) {
    return <div className={styles.page}><div className={styles.centered}>{error}</div></div>;
  }

  return (
    <div className={styles.page}>

      {/* Nav */}
      <header className={styles.nav}>
        <div className={styles.navLeft}>
          <span className={styles.logo}>
            <span className={styles.logoMark}>⬡</span>
            <span className={styles.logoText}>FHIR Portal</span>
          </span>
          <span className={styles.navBadge}>R4</span>
        </div>
        <div className={styles.navRight}>
          <Link href="/profile" className={styles.profileBtn}>
            <span className={styles.profileAvatar}>
              {patientName.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
            </span>
            <span className={styles.profileName}>{loading ? '…' : patientName}</span>
          </Link>
          <button className={styles.logoutBtn} onClick={() => authApi.logout()}>
            Sign out
          </button>
        </div>
      </header>

      {/* Main */}
      <main className={styles.main}>
        <div className={styles.pageHeader}>
          <div>
            <p className={styles.pageSubtitle}>{greeting}</p>
            <h1 className={styles.pageTitle}>
              {loading ? 'Loading…' : `${patientName}'s Dashboard`}
            </h1>
          </div>
          <div className={styles.patientId}>
            <span className={styles.idLabel}>Patient ID</span>
            <span className={styles.idValue}>{session?.patient_id ?? '—'}</span>
          </div>
        </div>

        {/* Resource Grid */}
        <div className={styles.grid}>
          {RESOURCE_CONFIG.map(r => (
            <ResourceCard
              key={r.key}
              title={r.title}
              code={r.code}
              accent={r.accent}
              description={r.description}
              data={fhirData[r.key]}
              loading={loading}
              extract={r.extract}
            />
          ))}
        </div>
      </main>

    </div>
  );
}