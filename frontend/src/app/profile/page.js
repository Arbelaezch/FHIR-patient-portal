'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApi, fhirApi } from '@/lib/fhirClient';
import styles from './profile.module.css';

export default function ProfilePage() {
  const router = useRouter();

  const [session, setSession] = useState(null);
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check session on mount
  useEffect(() => {
    authApi.getSession()
      .then(setSession)
      .catch(err => {
        if (err.status === 401) router.replace('/login');
      });
  }, [router]);

  // Fetch patient data once we have a patient ID
  useEffect(() => {
    if (!session?.patient_id) return;
    fhirApi.getPatient(session.patient_id)
      .then(setPatient)
      .finally(() => setLoading(false));
  }, [session]);

  // Derived display values
  const name = (() => {
    const n = patient?.name?.[0];
    if (!n) return '—';
    return [n.prefix?.join(' '), n.given?.join(' '), n.family].filter(Boolean).join(' ');
  })();

  const initials = name === '—' ? '?'
    : name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  const dob    = patient?.birthDate ?? '—';
  const gender = patient?.gender
    ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)
    : '—';
  const phone  = patient?.telecom?.find(t => t.system === 'phone')?.value ?? '—';
  const address = (() => {
    const a = patient?.address?.[0];
    if (!a) return '—';
    return [a.line?.join(' '), a.city, a.state, a.postalCode].filter(Boolean).join(', ');
  })();

  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <Link href="/" className={styles.back}>← Dashboard</Link>
        <span className={styles.navTitle}>Profile</span>
        <div style={{ width: 80 }} />
      </header>

      <main className={styles.main}>
        <div className={styles.card}>

          {/* Avatar + name */}
          <div className={styles.avatarSection}>
            <div className={styles.avatar}>
              {loading ? '…' : initials}
            </div>
            <div>
              <h1 className={styles.name}>{loading ? 'Loading…' : name}</h1>
              <p className={styles.handle}>Patient Account</p>
            </div>
          </div>

          <div className={styles.divider} />

          {/* Demographics */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Demographics</h2>
            <div className={styles.fieldGroup}>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Date of Birth</span>
                <span className={styles.fieldValue}>{loading ? '…' : dob}</span>
              </div>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Gender</span>
                <span className={styles.fieldValue}>{loading ? '…' : gender}</span>
              </div>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Phone</span>
                <span className={styles.fieldValue}>{loading ? '…' : phone}</span>
              </div>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Address</span>
                <span className={styles.fieldValue}>{loading ? '…' : address}</span>
              </div>
            </div>
          </div>

          <div className={styles.divider} />

          {/* Account */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Account</h2>
            <div className={styles.fieldGroup}>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Patient ID</span>
                <span className={styles.fieldValueMono}>
                  {loading ? '…' : session?.patient_id ?? '—'}
                </span>
              </div>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>FHIR Version</span>
                <span className={styles.fieldValueMono}>R4</span>
              </div>
              <div className={styles.field}>
                <span className={styles.fieldLabel}>Data Source</span>
                <span className={styles.fieldValue}>Epic MyChart</span>
              </div>
            </div>
          </div>

          <div className={styles.divider} />

          {/* Actions */}
          <div className={styles.actions}>
            <button
              className={styles.logoutBtn}
              onClick={() => authApi.logout()}
            >
              Sign out
            </button>
          </div>

        </div>
      </main>
    </div>
  );
}