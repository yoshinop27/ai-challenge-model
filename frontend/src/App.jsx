import FileDropZone from './components/FileDropZone'
import FormField from './components/FormField'
import { useFarmForm } from './hooks/useFarmForm'

export default function App() {
  const { fields, files, setFiles, errors, setField, handleSubmit } = useFarmForm()

  return (
    <div className="page">
      <div className="card">
        <h1 className="card-title">Farm Submission</h1>
        <p className="card-subtitle">Provide your farm details and upload supporting files</p>

        <form onSubmit={handleSubmit} noValidate>
          <FormField label="Farm Size (acres)" error={errors.farmSize}>
            <input
              className={`input${errors.farmSize ? ' error' : ''}`}
              type="number"
              min="0"
              step="any"
              placeholder="e.g. 250"
              value={fields.farmSize}
              onChange={setField('farmSize')}
            />
          </FormField>

          <div className="row">
            <FormField label="Latitude" error={errors.lat}>
              <input
                className={`input${errors.lat ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. 41.8781"
                value={fields.lat}
                onChange={setField('lat')}
              />
            </FormField>
            <FormField label="Longitude" error={errors.lng}>
              <input
                className={`input${errors.lng ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. −87.6298"
                value={fields.lng}
                onChange={setField('lng')}
              />
            </FormField>
          </div>

          <FormField label="Files" error={errors.files}>
            <FileDropZone files={files} onChange={setFiles} />
          </FormField>

          <button type="submit" className="submit-btn">Submit</button>
        </form>
      </div>
    </div>
  )
}
