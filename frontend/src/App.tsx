import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { EndUserPage } from './pages/EndUserPage';
import { BulkyWasteApply } from './pages/BulkyWasteApply';
import { OperatorLogin } from './pages/OperatorLogin';
import { InquiryList } from './pages/InquiryList';
import { InquiryDetail } from './pages/InquiryDetail';
import { OperatorAdd } from './pages/OperatorAdd';
import { OperatorList } from './pages/OperatorList';
import { BULKY_WASTE_APPLY_PATH } from './constants';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* エンドユーザ画面（プレヒアリング → チャット） */}
          <Route path="/" element={<EndUserPage />} />

          {/* 粗大ごみ申し込みページ（モック） */}
          <Route path={BULKY_WASTE_APPLY_PATH} element={<BulkyWasteApply />} />

          {/* オペレータ ログイン画面 */}
          <Route path="/operator/login" element={<OperatorLogin />} />

          {/* オペレータ 認証必須画面 */}
          <Route
            path="/operator/inquiries"
            element={
              <ProtectedRoute>
                <InquiryList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/inquiries/:id"
            element={
              <ProtectedRoute>
                <InquiryDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/users/add"
            element={
              <ProtectedRoute>
                <OperatorAdd />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/users"
            element={
              <ProtectedRoute>
                <OperatorList />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
