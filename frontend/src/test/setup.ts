/**
 * Impostazioni comuni dei test. jsdom non implementa lo scorrimento degli elementi,
 * che i menu a tendina di Naive UI usano per mostrare l'opzione scelta.
 */
if (typeof Element.prototype.scrollTo !== 'function') {
  Element.prototype.scrollTo = () => undefined
}
