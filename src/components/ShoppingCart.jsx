/**
 * ShoppingCart Component
 *
 * Full-featured shopping cart with quantity controls, item removal,
 * and real-time total calculation. Persists state to localStorage.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency } from '../utils/format';
import { CartItemCard } from './CartItemCard';
import { EmptyCart } from './EmptyCart';
import { CartBadge } from './CartBadge';
import { useToast } from '../hooks/useToast';
import api from '../services/api';

const CART_STORAGE_KEY = 'projectexpress_cart';
const MAX_QUANTITY = 99;
const MIN_QUANTITY = 1;

/**
 * Load cart from localStorage.
 * @returns {Array} Array of cart items
 */
function loadCartFromStorage() {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (err) {
    console.error('Failed to parse cart from localStorage:', err);
    return [];
  }
}

/**
 * Save cart to localStorage.
 * @param {Array} items - Cart items to persist
 */
function saveCartToStorage(items) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch (err) {
    console.error('Failed to save cart to localStorage:', err);
  }
}

export default function ShoppingCart() {
  const [items, setItems] = useState(loadCartFromStorage);
  const [isUpdating, setIsUpdating] = useState(false);
  const [promoCode, setPromoCode] = useState('');
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [promoError, setPromoError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Persist cart whenever it changes
  useEffect(() => {
    saveCartToStorage(items);
  }, [items]);

  // Calculate totals
  const subtotal = useMemo(
    () => items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [items]
  );

  const shipping = useMemo(
    () => (subtotal >= 50 ? 0 : 5.99),
    [subtotal]
  );

  const tax = useMemo(() => subtotal * 0.08, [subtotal]);

  const total = useMemo(
    () => subtotal + shipping + tax - promoDiscount,
    [subtotal, shipping, tax, promoDiscount]
  );

  const totalItems = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity, 0),
    [items]
  );

  /**
   * Update quantity for an item with optimistic UI.
   * @param {number} itemId - Product ID
   * @param {number} newQuantity - Desired quantity
   */
  const updateQuantity = useCallback(async (itemId, newQuantity) => {
    const clamped = Math.max(MIN_QUANTITY, Math.min(MAX_QUANTITY, newQuantity));
    const previousItems = items;

    // Optimistic update
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, quantity: clamped } : item
      )
    );

    try {
      await api.patch(`/cart/items/${itemId}`, { quantity: clamped });
    } catch (err) {
      // Rollback on failure
      setItems(previousItems);
      addToast('Failed to update quantity. Please try again.', 'error');
    }
  }, [items, addToast]);

  /**
   * Remove an item from the cart with confirmation.
   * @param {number} itemId - Product ID to remove
   * @param {string} itemName - Product name for confirmation message
   */
  const removeItem = useCallback(async (itemId, itemName) => {
    if (!window.confirm(`Remove "${itemName}" from your cart?`)) {
      return;
    }

    const previousItems = items;
    setItems((prev) => prev.filter((item) => item.id !== itemId));

    try {
      await api.delete(`/cart/items/${itemId}`);
      addToast(`"${itemName}" removed from cart`, 'info');
    } catch (err) {
      setItems(previousItems);
      addToast('Failed to remove item. Please try again.', 'error');
    }
  }, [items, addToast]);

  /**
   * Apply a promo code.
   */
  const handleApplyPromo = useCallback(async () => {
    if (!promoCode.trim()) return;

    setIsUpdating(true);
    setPromoError('');

    try {
      const response = await api.post('/cart/promo', { code: promoCode.trim() });
      setPromoDiscount(response.data.discount);
      addToast('Promo code applied!', 'success');
    } catch (err) {
      setPromoError(err.response?.data?.message || 'Invalid promo code');
      setPromoDiscount(0);
    } finally {
      setIsUpdating(false);
    }
  }, [promoCode, addToast]);

  /**
   * Proceed to checkout.
   */
  const handleCheckout = useCallback(() => {
    if (items.length === 0) {
      addToast('Your cart is empty', 'warning');
      return;
    }

    if (!user) {
      addToast('Please log in to continue checkout', 'info');
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }

    navigate('/checkout');
  }, [items, user, navigate, addToast]);

  if (items.length === 0) {
    return (
      <div className="shopping-cart-page">
        <h1>Shopping Cart</h1>
        <EmptyCart />
      </div>
    );
  }

  return (
    <div className="shopping-cart-page">
      <h1>Shopping Cart ({totalItems} items)</h1>

      <div className="cart-layout">
        <div className="cart-items-list">
          {items.map((item) => (
            <CartItemCard
              key={item.id}
              item={item}
              onUpdateQuantity={updateQuantity}
              onRemove={removeItem}
              minQuantity={MIN_QUANTITY}
              maxQuantity={MAX_QUANTITY}
            />
          ))}
        </div>

        <div className="cart-summary">
          <h2>Order Summary</h2>

          <div className="summary-line">
            <span>Subtotal</span>
            <span>{formatCurrency(subtotal)}</span>
          </div>

          <div className="summary-line">
            <span>Shipping</span>
            <span>{shipping === 0 ? 'FREE' : formatCurrency(shipping)}</span>
          </div>

          {shipping > 0 && (
            <div className="free-shipping-notice">
              Add {formatCurrency(50 - subtotal)} more for free shipping!
            </div>
          )}

          <div className="summary-line">
            <span>Tax (estimated)</span>
            <span>{formatCurrency(tax)}</span>
          </div>

          {promoDiscount > 0 && (
            <div className="summary-line discount">
              <span>Promo discount</span>
              <span>-{formatCurrency(promoDiscount)}</span>
            </div>
          )}

          <div className="promo-section">
            <input
              type="text"
              placeholder="Enter promo code"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
              disabled={isUpdating}
              className="promo-input"
              aria-label="Promo code"
            />
            <button
              onClick={handleApplyPromo}
              disabled={isUpdating || !promoCode.trim()}
              className="promo-button"
            >
              Apply
            </button>
          </div>

          {promoError && <p className="promo-error">{promoError}</p>}

          <div className="summary-total">
            <span>Total</span>
            <span>{formatCurrency(Math.max(0, total))}</span>
          </div>

          <button
            onClick={handleCheckout}
            className="checkout-button"
            disabled={items.length === 0}
          >
            Proceed to Checkout
          </button>

          <Link to="/products" className="continue-shopping-link">
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}
