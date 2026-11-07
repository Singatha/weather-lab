import { useQuery } from '@tanstack/react-query'
import { useId, useState } from 'react'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { searchLocations } from '../services/api'
import type { Location } from '../types/weather'

interface LocationSearchProps {
  onNoResults: () => void
  onSelect: (location: Location) => void
}

export function LocationSearch({ onNoResults, onSelect }: LocationSearchProps) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const listboxId = useId()
  const debouncedQuery = useDebouncedValue(query.trim(), 350)
  const searchQuery = useQuery({
    queryKey: ['locations', debouncedQuery],
    queryFn: ({ signal }) => searchLocations(debouncedQuery, signal),
    enabled: debouncedQuery.length >= 2,
    staleTime: 24 * 60 * 60 * 1000,
    retry: 1,
  })
  const locations = searchQuery.data?.locations ?? []

  const chooseLocation = (location: Location) => {
    setQuery('')
    setIsOpen(false)
    setActiveIndex(-1)
    onSelect(location)
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const submittedQuery = query.trim()
    if (submittedQuery.length < 2) return

    if (activeIndex >= 0 && locations[activeIndex]) {
      chooseLocation(locations[activeIndex])
      return
    }

    try {
      const response =
        submittedQuery === debouncedQuery && searchQuery.data
          ? searchQuery.data
          : await searchLocations(submittedQuery)
      if (response.locations[0]) chooseLocation(response.locations[0])
      else {
        setIsOpen(false)
        onNoResults()
      }
    } catch {
      setIsOpen(true)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || locations.length === 0) {
      if (event.key === 'ArrowDown' && query.trim().length >= 2) setIsOpen(true)
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => (index + 1) % locations.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => (index <= 0 ? locations.length - 1 : index - 1))
    } else if (event.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const showPopover = isOpen && debouncedQuery.length >= 2

  return (
    <form className="search-form" onSubmit={submit} role="search">
      <div className="search-field-wrap">
        <img alt="" aria-hidden="true" className="search-icon" src="/assets/images/icon-search.svg" />
        <input
          aria-activedescendant={
            activeIndex >= 0 ? `${listboxId}-option-${activeIndex}` : undefined
          }
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={showPopover}
          aria-label="Search for a place"
          autoComplete="off"
          className="search-input"
          onBlur={() => window.setTimeout(() => setIsOpen(false), 150)}
          onChange={(event) => {
            setQuery(event.target.value)
            setIsOpen(true)
            setActiveIndex(-1)
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search for a place..."
          role="combobox"
          value={query}
        />

        {showPopover && (
          <div className="suggestions" id={listboxId} role="listbox">
            {searchQuery.isFetching && (
              <div aria-live="polite" className="search-status">
                <img alt="" aria-hidden="true" className="spin" src="/assets/images/icon-loading.svg" />
                Search in progress
              </div>
            )}
            {!searchQuery.isFetching && searchQuery.isError && (
              <div aria-live="polite" className="search-status">
                Search is unavailable. Please try again.
              </div>
            )}
            {!searchQuery.isFetching && !searchQuery.isError && locations.length === 0 && (
              <div aria-live="polite" className="search-status">No matching places</div>
            )}
            {!searchQuery.isFetching &&
              locations.map((location, index) => (
                <button
                  aria-selected={activeIndex === index}
                  className="suggestion"
                  id={`${listboxId}-option-${index}`}
                  key={`${location.id}-${location.latitude}-${location.longitude}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => chooseLocation(location)}
                  role="option"
                  type="button"
                >
                  <span>{location.name}, {location.country}</span>
                  {location.region && <small>{location.region}</small>}
                </button>
              ))}
          </div>
        )}
      </div>
      <button className="search-button" type="submit">
        Search
      </button>
    </form>
  )
}
