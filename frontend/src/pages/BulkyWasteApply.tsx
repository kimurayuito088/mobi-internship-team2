import { useState } from 'react';
import {
  APPLY_CONTACT,
  APPLY_GUIDE_LINKS,
  APPLY_MENU_ITEMS,
} from '../constants/bulkyWasteApply';
import styles from './BulkyWasteApply.module.css';

/**
 * 粗大ごみ申し込みページのモック。
 * 実際の受付システムは存在しないため、自治体のインターネット受付を模した静的画面のみ提供する。
 */
export function BulkyWasteApply() {
  const [selectedMenuLabel, setSelectedMenuLabel] = useState<string | null>(null);

  return (
    <div className={styles.container} data-testid="bulky-waste-apply">
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>粗大ごみ受付事務所 インターネット受付</h1>
        <p className={styles.headerSubtext}>お手続きの種類を選択してください</p>
      </header>

      <p className={styles.mockNotice}>
        ※ このページは動作確認用のモックです。実際のお申し込みはできません。
      </p>

      <nav className={styles.guideLinks} aria-label="案内">
        {APPLY_GUIDE_LINKS.map((link) => (
          <span key={link} className={styles.guideLink}>
            {link}
          </span>
        ))}
      </nav>

      <main className={styles.body}>
        <ul className={styles.menuList}>
          {APPLY_MENU_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={styles.menuButton}
                onClick={() => setSelectedMenuLabel(item.label)}
                data-testid={`apply-menu-${item.id}`}
              >
                <span className={styles.menuLabel}>{item.label}</span>
                <span className={styles.menuDescription}>{item.description}</span>
              </button>
            </li>
          ))}
        </ul>

        {selectedMenuLabel !== null && (
          <p className={styles.menuNotice} role="status" data-testid="apply-menu-notice">
            「{selectedMenuLabel}」の手続き画面はモックのため用意されていません。
          </p>
        )}

        <section className={styles.contactBox}>
          <h2 className={styles.contactTitle}>お申し込み・お問い合わせ</h2>
          <p className={styles.contactLine}>{APPLY_CONTACT.officeName}</p>
          <p className={styles.contactLine}>電話番号：{APPLY_CONTACT.phoneNumber}</p>
          <p className={styles.contactLine}>{APPLY_CONTACT.businessHours}</p>
          <p className={styles.contactNote}>（{APPLY_CONTACT.closedDays}）</p>
        </section>
      </main>
    </div>
  );
}
