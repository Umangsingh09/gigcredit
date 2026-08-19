import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Layout({ children, currentPage, onNavigate }) {
  return (
    <div className="app-layout">
      <Sidebar
        currentPage={currentPage}
        onNavigate={onNavigate}
      />

      <div className="main-area">
        <Topbar currentPage={currentPage} />

        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;