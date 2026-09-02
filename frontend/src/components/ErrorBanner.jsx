export default function ErrorBanner({ erro }) {
  if (!erro) return null;
  return (
    <div className="error-banner" role="alert">
      {erro}
    </div>
  );
}
