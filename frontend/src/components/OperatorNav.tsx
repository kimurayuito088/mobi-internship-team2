import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import styles from './OperatorNav.module.css';

/**
 * オペレータ用ナビゲーションバー
 */
export function OperatorNav() {
  const { operator, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className={styles.nav} data-testid="operator-nav">
      <div className={styles.left}>
        <Link to="/operator/inquiries" className={styles.link}>問い合わせ一覧</Link>
        <Link to="/operator/users" className={styles.link}>オペレータ管理</Link>
      </div>
      <div className={styles.right}>
        <span className={styles.operatorName}>{operator?.display_name}</span>
        <button
          className={styles.logoutButton}
          onClick={handleLogout}
          data-testid="operator-nav-logout-button"
        >
          ログアウト
        </button>
      </div>
    </nav>
  );
}
