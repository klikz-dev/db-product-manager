tag = "trade" #customer tag
cartTotal = Input.cart.subtotal_price_was #total cart price
cartNum = 0
freeshipping = "FREE SHIPPING" 
customer = Input.cart.customer
limit = Money.new(cents:100) * 125

hasAllFreeSamples = true
unless Input.cart.line_items.all? { |line_item| line_item.variant.title.include?("Sample") }
  Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name == 'Free Shipping for Samples'}
  hasAllFreeSamples = false
end

Input.cart.line_items.each do |line_item|
  cartNum += line_item.quantity
end

has_white_glove_tag = Input.cart.line_items.all? { |line_item| line_item.variant.product.tags.include?("White Glove") }

# 5/9/23 Disable white glove shipping - from bk
has_white_glove_tag = false

if has_white_glove_tag
  Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name != 'White Glove Shipping'}
else
  Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name == 'White Glove Shipping'}

  if cartTotal > limit && !hasAllFreeSamples
    if customer
      if customer.tags.include?(tag)
        Input.shipping_rates.delete_if do |shipping_rate|
          shipping_rate.name.start_with?("Free Shipping")
        end
      else
        Input.shipping_rates.delete_if do |shipping_rate|
          shipping_rate.name.start_with?("UPS® Ground")
        end
      end
    else
      Input.shipping_rates.delete_if do |shipping_rate|
        shipping_rate.name.start_with?("UPS® Ground")
      end
    end
    
    Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.start_with?("2nd Day Shipping for Samples")
    end
    Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.start_with?("Overnight Shipping for Samples")
    end
    
    Output.shipping_rates = Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.upcase.start_with?("UPS GROUND")
    end

  elsif hasAllFreeSamples
    if cartNum < 6
      Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 1' and shipping_rate.name != 'Overnight Shipping for Samples - 1'}
    elsif cartNum < 11
      Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 2' and shipping_rate.name != 'Overnight Shipping for Samples - 2'}
    else
      Input.shipping_rates.delete_if { |shipping_rate| shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 3' and shipping_rate.name != 'Overnight Shipping for Samples - 3'}
    end

  else
    Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.start_with?("Free Shipping")
    end
    Input.shipping_rates.delete_if do |shipping_rate|
        shipping_rate.name.start_with?("UPS® Ground")
    end
    Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.start_with?("2nd Day Shipping for Samples")
    end
    Input.shipping_rates.delete_if do |shipping_rate|
      shipping_rate.name.start_with?("Overnight Shipping for Samples")
    end
  end
end

Output.shipping_rates = Input.shipping_rates
