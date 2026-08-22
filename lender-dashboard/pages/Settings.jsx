import { useEffect, useState } from "react";

import { defaultSettings, getSettings, updateSettings } from "../src/data/api";

function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [status, setStatus] = useState("");

  useEffect(() => {
    getSettings().then(setSettings).catch(() => setStatus("Using local settings until the API is connected."));
  }, []);

  const handleChange = (event) => {
    const { name, type, checked, value } = event.target;
    setSettings((current) => ({ ...current, [name]: type === "checkbox" ? checked : Number(value) }));
    setStatus("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const saved = await updateSettings(settings);
      setSettings(saved);
      setStatus("Settings saved to the backend.");
    } catch {
      setStatus("Settings saved for this session. Connect the API to persist them.");
    }
  };

  return (
    <section className="management-page">
      <div className="page-intro"><div><p className="eyebrow">WORKSPACE CONTROL</p><h2>Settings</h2><p>Configure review rules and lender notifications.</p></div></div>
      <form className="settings-panel" onSubmit={handleSubmit}>
        <div className="settings-section"><div><h3>Review workflow</h3><p>Set the minimum score used to flag applications for manual review.</p></div><label className="setting-control"><span>Review threshold</span><input name="review_threshold" type="number" min="300" max="900" value={settings.review_threshold} onChange={handleChange} /></label></div>
        <div className="settings-section"><div><h3>Refresh interval</h3><p>Choose how often dashboard data should refresh.</p></div><label className="setting-control"><span>Minutes</span><input name="auto_refresh_minutes" type="number" min="1" max="120" value={settings.auto_refresh_minutes} onChange={handleChange} /></label></div>
        <div className="settings-section"><div><h3>Notifications</h3><p>Keep the team informed about important portfolio activity.</p></div><div className="toggle-list"><label><input name="email_notifications" type="checkbox" checked={settings.email_notifications} onChange={handleChange} /> Email notifications</label><label><input name="weekly_report" type="checkbox" checked={settings.weekly_report} onChange={handleChange} /> Weekly portfolio report</label></div></div>
        <div className="settings-actions"><span>{status}</span><button className="primary-button" type="submit">Save settings</button></div>
      </form>
    </section>
  );
}

export default Settings;
