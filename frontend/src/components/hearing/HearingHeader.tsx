import styles from '../../pages/PreHearing.module.css';

export function HearingHeader() {
  return (
    <header className={styles.header}>
      <h1 className={styles.headerTitle}>お問い合わせ</h1>
      <p className={styles.headerSubtext}>選択肢をタップしてお進みください</p>
    </header>
  );
}
