import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Layout({ children, currentPage, onNavigate, onLogout, profile }) {
  return (
    <div className="app-layout">
      <Sidebar
        currentPage={currentPage}
        onNavigate={onNavigate}
      />

      <div className="main-area">
        <Topbar currentPage={currentPage} onLogout={onLogout} profile={profile} />

        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;