import { useEffect, useRef, useState } from 'react'
import {
  IMPERIAL_UNITS,
  METRIC_UNITS,
  type PrecipitationUnit,
  type TemperatureUnit,
  type UnitSettings,
  type WindUnit,
} from '../utils/units'

interface UnitSelectorProps {
  value: UnitSettings
  onChange: (units: UnitSettings) => void
}

interface OptionProps {
  checked: boolean
  children: React.ReactNode
  onSelect: () => void
}

function UnitOption({ checked, children, onSelect }: OptionProps) {
  return (
    <button
      aria-checked={checked}
      className="unit-option"
      onClick={onSelect}
      role="menuitemradio"
      type="button"
    >
      <span>{children}</span>
      {checked && <img alt="" aria-hidden="true" src="/assets/images/icon-checkmark.svg" />}
    </button>
  )
}

export function UnitSelector({ value, onChange }: UnitSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const isMetric =
    value.temperature === 'celsius' &&
    value.wind === 'km/h' &&
    value.precipitation === 'mm'

  useEffect(() => {
    if (!isOpen) return

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setIsOpen(false)
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('mousedown', closeOnOutsideClick)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [isOpen])

  const setTemperature = (temperature: TemperatureUnit) =>
    onChange({ ...value, temperature })
  const setWind = (wind: WindUnit) => onChange({ ...value, wind })
  const setPrecipitation = (precipitation: PrecipitationUnit) =>
    onChange({ ...value, precipitation })

  return (
    <div className="unit-selector" ref={containerRef}>
      <button
        aria-expanded={isOpen}
        aria-haspopup="menu"
        className="unit-trigger"
        onClick={() => setIsOpen((open) => !open)}
        type="button"
      >
        <img alt="" aria-hidden="true" src="/assets/images/icon-units.svg" />
        <span>Units</span>
        <img alt="" aria-hidden="true" className="chevron" src="/assets/images/icon-dropdown.svg" />
      </button>

      {isOpen && (
        <div aria-label="Measurement units" className="unit-menu" role="menu">
          <button
            className="unit-switch"
            onClick={() => onChange(isMetric ? IMPERIAL_UNITS : METRIC_UNITS)}
            role="menuitem"
            type="button"
          >
            Switch to {isMetric ? 'Imperial' : 'Metric'}
          </button>

          <div aria-label="Temperature" className="unit-group" role="group">
            <p>Temperature</p>
            <UnitOption
              checked={value.temperature === 'celsius'}
              onSelect={() => setTemperature('celsius')}
            >
              Celsius (°C)
            </UnitOption>
            <UnitOption
              checked={value.temperature === 'fahrenheit'}
              onSelect={() => setTemperature('fahrenheit')}
            >
              Fahrenheit (°F)
            </UnitOption>
          </div>

          <div aria-label="Wind speed" className="unit-group" role="group">
            <p>Wind Speed</p>
            <UnitOption checked={value.wind === 'km/h'} onSelect={() => setWind('km/h')}>
              km/h
            </UnitOption>
            <UnitOption checked={value.wind === 'mph'} onSelect={() => setWind('mph')}>
              mph
            </UnitOption>
          </div>

          <div aria-label="Precipitation" className="unit-group" role="group">
            <p>Precipitation</p>
            <UnitOption
              checked={value.precipitation === 'mm'}
              onSelect={() => setPrecipitation('mm')}
            >
              Millimeters (mm)
            </UnitOption>
            <UnitOption
              checked={value.precipitation === 'in'}
              onSelect={() => setPrecipitation('in')}
            >
              Inches (in)
            </UnitOption>
          </div>
        </div>
      )}
    </div>
  )
}
