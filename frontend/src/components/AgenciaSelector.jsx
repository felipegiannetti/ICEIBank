import { useState } from "react";
import { getAgenciaUrl, setAgenciaUrl } from "../api/client";

const AGENCIAS_PADRAO = [
  { label: "Agência 0 (porta 4000)", url: "http://localhost:4000" },
  { label: "Agência 1 (porta 4001)", url: "http://localhost:4001" },
  { label: "Agência 2 (porta 4002)", url: "http://localhost:4002" },
];

export default function AgenciaSelector() {
  const [url, setUrl] = useState(getAgenciaUrl());

  function aoMudar(novaUrl) {
    setUrl(novaUrl);
    setAgenciaUrl(novaUrl);
  }

  return (
    <div className="agencia-selector">
      <label htmlFor="agencia-select">Agência (porta de entrada)</label>
      <select id="agencia-select" value={url} onChange={(e) => aoMudar(e.target.value)}>
        {AGENCIAS_PADRAO.map((a) => (
          <option key={a.url} value={a.url}>
            {a.label}
          </option>
        ))}
        {!AGENCIAS_PADRAO.some((a) => a.url === url) && (
          <option value={url}>Personalizada ({url})</option>
        )}
      </select>
      <input
        type="text"
        value={url}
        onChange={(e) => aoMudar(e.target.value)}
        placeholder="ou digite uma URL customizada"
      />
    </div>
  );
}
