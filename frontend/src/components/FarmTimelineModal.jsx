const TYPE_META = {
  plant:     { icon: '🌱', color: '#4ade80',  label: 'Plant'     },
  harvest:   { icon: '🌾', color: '#c9a84c',  label: 'Harvest'   },
  fertilize: { icon: '🧪', color: '#818cf8',  label: 'Fertilize' },
  irrigate:  { icon: '💧', color: '#38bdf8',  label: 'Irrigate'  },
  spray:     { icon: '🛡️', color: '#fb923c',  label: 'Spray'     },
  prepare:   { icon: '⛏️', color: '#94a3b8',  label: 'Prepare'   },
  monitor:   { icon: '🔍', color: '#a3e635',  label: 'Monitor'   },
  other:     { icon: '📋', color: '#888888',  label: 'Other'     },
}

function PhaseCard({ phase, window: win, type, because, actions = [], index, total }) {
  const meta = TYPE_META[type] ?? TYPE_META.other
  const isLast = index === total - 1
  return (
    <div className="tl3-phase-wrap">
      <div className="tl3-phase" style={{ '--pc': meta.color }}>
        {/* Step number + type badge */}
        <div className="tl3-phase-top">
          <span className="tl3-step-num">{index + 1}</span>
          <span className="tl3-type-badge">
            <span>{meta.icon}</span>
            <span>{meta.label}</span>
          </span>
          <span className="tl3-window">{win}</span>
        </div>

        {/* Phase name */}
        <h3 className="tl3-phase-name">{phase}</h3>

        {/* Because reasoning */}
        {because && (
          <div className="tl3-because">
            <span className="tl3-because-label">Why now</span>
            <p className="tl3-because-text">{because}</p>
          </div>
        )}

        {/* Actions */}
        {actions.length > 0 && (
          <ul className="tl3-actions">
            {actions.map((a, i) => (
              <li key={i} className="tl3-action">{a}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Connector arrow */}
      {!isLast && (
        <div className="tl3-connector">
          <div className="tl3-connector-line" />
          <span className="tl3-connector-arrow">↓</span>
        </div>
      )}
    </div>
  )
}

export default function FarmTimelineModal({ timeline, onClose }) {
  if (!timeline) return null
  const { weather_outlook, summary, phases = [] } = timeline

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="tl3-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="tl3-header">
          <div>
            <div className="tl3-title">Farm Growing Plan</div>
            <div className="tl3-subtitle">Soil-matched lifecycle · plant to harvest</div>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {/* Overview cards */}
        {(weather_outlook || summary) && (
          <div className="tl3-overview">
            {weather_outlook && (
              <div className="tl3-ov-card tl3-ov-weather">
                <span className="tl3-ov-label">📡 Near-term Forecast</span>
                <p className="tl3-ov-text">{weather_outlook}</p>
              </div>
            )}
            {summary && (
              <div className="tl3-ov-card tl3-ov-strategy">
                <span className="tl3-ov-label">🌿 Seasonal Strategy</span>
                <p className="tl3-ov-text">{summary}</p>
              </div>
            )}
          </div>
        )}

        {/* Phase flow */}
        <div className="tl3-body">
          {phases.length === 0 ? (
            <p style={{ color: '#666', fontSize: '0.9rem', padding: '1rem 0' }}>No phases generated.</p>
          ) : (
            <div className="tl3-phases">
              {phases.map((p, i) => (
                <PhaseCard
                  key={i}
                  index={i}
                  total={phases.length}
                  phase={p.phase}
                  window={p.window}
                  type={p.type}
                  because={p.because}
                  actions={p.actions ?? []}
                />
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
