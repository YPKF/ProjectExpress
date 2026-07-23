// Cart Persistence Hook
const useCartPersist = (cart) => {
  useEffect(() => {
    localStorage.setItem("cart", JSON.stringify(cart));
  }, [cart]);
};
