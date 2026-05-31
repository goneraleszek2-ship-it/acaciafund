import { atom } from 'nanostores'

// Create an atom (store) with initial values
export const bayesState = atom({
  prior: 0.5,
  likelihood: 0.7,
  posterior: 0.35 // initial posterior based on default values
})

// Helper function to calculate posterior from prior and likelihood
export const calculatePosterior = (prior, likelihood) => {
  return (prior * likelihood) / (prior * likelihood + (1 - prior) * (1 - likelihood))
}