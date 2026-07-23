// Shopping Cart Component
const ShoppingCart = ({ items, onUpdateQuantity, onRemove }) => {
  return (
    <div className="cart">
      {items.map(item => (
        <CartItem key={item.id} item={item} />
      ))}
    </div>
  );
};
