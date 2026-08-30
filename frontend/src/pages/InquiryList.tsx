import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { OperatorNav } from '../components/OperatorNav';
import { StatusBadge } from '../components/StatusBadge';
import { AssignButton } from '../components/AssignButton';
import { InquiryWithStatus, InquiryGroup, GroupedInquiryResponse } from '../types';
import {
  API_BASE_URL,
  UNANSWERED_LIMIT,
  MINE_LIMIT,
  CLOSED_LIMIT,
  GROUP_POLL_INTERVAL_MS,
} from '../constants';
import { getHearingCategoryShortLabel } from '../constants/hearingFlow';
import styles from './InquiryList.module.css';

const EMPTY_GROUP: InquiryGroup = { items: [], total: 0, has_more: false };

const EMPTY_GROUPED: GroupedInquiryResponse = {
  unanswered: EMPTY_GROUP,
  mine: EMPTY_GROUP,
  closed: EMPTY_GROUP,
};

interface InquiryGroupPanelProps {
  title: string;
  groupKey: 'unanswered' | 'mine' | 'closed';
  group: InquiryGroup;
  emptyMessage: string;
  showAssignButton: boolean;
  onAssign: (inquiryId: number) => void;
  onRowClick: (inquiry: InquiryWithStatus) => void;
}

/**
 * 問い合わせグループ1枠分のテーブル
 */
function InquiryGroupPanel({
  title,
  groupKey,
  group,
  emptyMessage,
  showAssignButton,
  onAssign,
  onRowClick,
}: InquiryGroupPanelProps) {
  return (
    <section className={styles.panel}>
      <header className={styles.panelHeader}>
        <h3 className={styles.panelTitle}>{title}</h3>
        <span className={styles.panelTotal}>{group.total}件</span>
      </header>
      {group.has_more && (
        <p className={styles.panelMeta}>
          全{group.total}件中{group.items.length}件を表示
        </p>
      )}
      <div className={styles.panelBody}>
        <table className={styles.table} data-testid={`inquiry-table-${groupKey}`}>
          <thead>
            <tr>
              <th>ID</th>
              <th>種類</th>
              <th>ステータス</th>
              <th>作成日時</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {group.items.length === 0 ? (
              <tr>
                <td colSpan={5} className={styles.empty}>{emptyMessage}</td>
              </tr>
            ) : (
              group.items.map(inquiry => {
                const isInputting = inquiry.display_status === 'inputting';
                return (
                  <tr
                    key={inquiry.id}
                    className={isInputting ? styles.rowDisabled : styles.row}
                    onClick={() => onRowClick(inquiry)}
                    data-testid={`inquiry-row-${inquiry.id}`}
                  >
                    <td>
                      <span className={styles.inquiryId}>#{inquiry.id}</span>
                      {groupKey === 'mine' && inquiry.has_unread && (
                        <span className={styles.unreadBadge}>新着</span>
                      )}
                    </td>
                    <td>{getHearingCategoryShortLabel(inquiry.category_id)}</td>
                    <td><StatusBadge status={inquiry.display_status} /></td>
                    <td>{new Date(inquiry.created_at).toLocaleString('ja-JP')}</td>
                    <td onClick={e => e.stopPropagation()}>
                      {showAssignButton && inquiry.display_status === 'waiting' && (
                        <AssignButton
                          inquiryId={inquiry.id}
                          onAssign={onAssign}
                          disabled={false}
                        />
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/**
 * 問い合わせ一覧画面（未返信 / 自分の担当 / クローズした案件の3枠）
 * 5秒間隔でグループAPIを再取得する
 */
export function InquiryList() {
  const { operator } = useAuth();
  const navigate = useNavigate();
  const [grouped, setGrouped] = useState<GroupedInquiryResponse>(EMPTY_GROUPED);
  const [isLoading, setIsLoading] = useState(false);
  const isFetchingRef = useRef(false);
  const hasLoadedOnceRef = useRef(false);

  const fetchGrouped = useCallback(async () => {
    if (!operator) return;
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    if (!hasLoadedOnceRef.current) {
      setIsLoading(true);
    }

    try {
      const params = new URLSearchParams({
        unanswered_limit: String(UNANSWERED_LIMIT),
        mine_limit: String(MINE_LIMIT),
        closed_limit: String(CLOSED_LIMIT),
      });
      const response = await fetch(
        `${API_BASE_URL}/inquiries/grouped?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('取得に失敗しました');

      const data: GroupedInquiryResponse = await response.json();
      setGrouped(data);
      hasLoadedOnceRef.current = true;
    } catch (error) {
      console.error('問い合わせ一覧取得エラー:', error);
    } finally {
      isFetchingRef.current = false;
      setIsLoading(false);
    }
  }, [operator]);

  useEffect(() => {
    if (!operator) return;

    void fetchGrouped();
    const intervalId = setInterval(() => {
      void fetchGrouped();
    }, GROUP_POLL_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [operator, fetchGrouped]);

  const handleAssign = async (inquiryId: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/inquiries/${inquiryId}/assign`,
        { method: 'POST', credentials: 'include' }
      );
      if (!response.ok) {
        const error = await response.json();
        alert(error.detail || '担当取得に失敗しました');
        return;
      }
      void fetchGrouped();
    } catch {
      alert('担当取得に失敗しました');
    }
  };

  const handleRowClick = (inquiry: InquiryWithStatus) => {
    if (inquiry.display_status === 'inputting') return;
    navigate(`/operator/inquiries/${inquiry.id}`);
  };

  return (
    <div className={styles.container}>
      <OperatorNav />
      <main className={styles.main}>
        <h2 className={styles.title}>問い合わせ一覧</h2>

        {isLoading ? (
          <p>読み込み中...</p>
        ) : (
          <div className={styles.layout}>
            <div className={styles.unanswered}>
              <InquiryGroupPanel
                title="未返信"
                groupKey="unanswered"
                group={grouped.unanswered}
                emptyMessage="未返信の問い合わせはありません"
                showAssignButton={true}
                onAssign={handleAssign}
                onRowClick={handleRowClick}
              />
            </div>
            <div className={styles.mine}>
              <InquiryGroupPanel
                title="自分の担当"
                groupKey="mine"
                group={grouped.mine}
                emptyMessage="自分の担当の問い合わせはありません"
                showAssignButton={false}
                onAssign={handleAssign}
                onRowClick={handleRowClick}
              />
            </div>
            <div className={styles.closed}>
              <InquiryGroupPanel
                title="クローズした案件"
                groupKey="closed"
                group={grouped.closed}
                emptyMessage="クローズした問い合わせはありません"
                showAssignButton={false}
                onAssign={handleAssign}
                onRowClick={handleRowClick}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
