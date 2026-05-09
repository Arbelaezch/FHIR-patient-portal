'use client';
import { authApi } from '@/lib/fhirClient';
import styles from './login.module.css';

export default function LoginPage() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>

        <div className={styles.header}>
          <span className={styles.logoMark}>⬡</span>
          <h1 className={styles.title}>FHIR Portal</h1>
          <p className={styles.subtitle}>Sign in to your health dashboard</p>
        </div>

        <div className={styles.card}>
          <p className={styles.description}>
            This portal connects to your Epic health record via SMART on FHIR.
            Click below to authenticate securely through MyChart.
          </p>
          <button className={styles.submitBtn} onClick={() => authApi.login()}>
            Connect with Epic
          </button>
        </div>

        <p className={styles.footer}>
          <span className={styles.footerMono}>FHIR R4</span> · Secure health data portal
        </p>

      </main>
    </div>
  );
}