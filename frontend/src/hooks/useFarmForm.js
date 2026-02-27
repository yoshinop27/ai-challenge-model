import { useState } from 'react'

const INITIAL_FIELDS = { farmSize: '', lat: '', lng: '' }

function validate(fields, files) {
  const errs = {}
  if (!fields.farmSize || isNaN(fields.farmSize) || Number(fields.farmSize) <= 0)
    errs.farmSize = 'Enter a valid farm size (acres)'
  if (!fields.lat || isNaN(fields.lat) || Math.abs(Number(fields.lat)) > 90)
    errs.lat = 'Enter a valid latitude (−90 to 90)'
  if (!fields.lng || isNaN(fields.lng) || Math.abs(Number(fields.lng)) > 180)
    errs.lng = 'Enter a valid longitude (−180 to 180)'
  if (files.length === 0)
    errs.files = 'Upload at least one file'
  return errs
}

export function useFarmForm() {
  const [fields, setFields] = useState(INITIAL_FIELDS)
  const [files, setFiles] = useState([])
  const [errors, setErrors] = useState({})

  const setField = (key) => (e) =>
    setFields((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate(fields, files)
    setErrors(errs)
    if (Object.keys(errs).length === 0) {
      console.log('Submitting', { ...fields, files })
    }
  }

  return { fields, files, setFiles, errors, setField, handleSubmit }
}
