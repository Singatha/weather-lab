import type { UnitSettings } from '../utils/units'
import { UnitSelector } from './UnitSelector'

interface HeaderProps {
  units: UnitSettings
  onUnitsChange: (units: UnitSettings) => void
}

export function Header({ units, onUnitsChange }: HeaderProps) {
  return (
    <header className="site-header">
      <img alt="Weather Now" className="logo" src="/assets/images/logo.svg" />
      <UnitSelector onChange={onUnitsChange} value={units} />
    </header>
  )
}
