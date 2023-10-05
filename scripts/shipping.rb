# ================================================================
# UpdateShippingRates
#
# Decides white glove shipping based on product tags
# Free shipping is eligible for non-trade customers when the order
# total is bigger than $125
# Sample shipping rates are decided by number of items in the cart
# Euro and multi brands disable expedited shipping
# ================================================================

class UpdateShippingRates
  def initialize(cart)
    EUROPEAN_BRANDS = "Aldeco Fabric,Alhambra Fabric,Christian Fischbacher Fabric,Colony Fabric,Colony Wallpaper,Jean Paul Gaultier Fabric,Jean Paul Gaultier Wallpaper,JWall Wallpaper,Lelievre Fabric,Lelievre Wallpaper,MissoniHome Wallpaper,Nicolette Mayer Fabric,Nicolette Mayer Wallpaper,Tassinari & Chatel Fabric,JF Fabrics Wallpaper,JF Fabrics Fabric,Maxwell Wallpaper,Maxwell Fabric,Andrew Martin Fabric,Andrew Martin Wallpaper,Baker Lifestyle Fabric,Baker Lifestyle Wallpaper,Baker Lifestyle Trim,Brunschwig & Fils Fabric,Brunschwig & Fils Wallpaper,Brunschwig & Fils Trim,Cole & Son Fabric,Cole & Son Wallpaper,Cole & Son Trim,G P & J Baker Fabric,G P & J Baker Wallpaper,G P & J Baker Trim,Gaston Y Daniela Fabric,Gaston Y Daniela Wallpaper,Lee Jofa Fabric,Lee Jofa Wallpaper,Lee Jofa Trim,Lizzo Fabric,Lizzo Wallpaper,Mulberry Fabric,Mulberry Wallpaper,Mulberry Trim,Threads Fabric,Threads Wallpaper,Threads Trim,Clarke & Clarke Fabric,Clarke & Clarke Wallpaper,Clarke & Clarke Trim,Morris & co Fabric,Morris & co Wallpaper,Harlequin Fabric,Harlequin Wallpaper,Sanderson Fabric,Sanderson Wallpaper,Scion Fabric,Scion Wallpaper,Zoffany Fabric,Zoffany Wallpaper,Tres Tintas Wallpaper,MindTheGap Fabric,MindTheGap Pillow,MindTheGap Wallpaper"
    @isTrade = !cart.customer.nil? && cart.customer.tags.include?('trade')

    @isWhileGlove = cart.line_items.any? { |line_item| line_item.variant.product.tags.include?("White Glove") }
    # @isWhileGlove = false

    @freeShippingEligible = cart.subtotal_price_was > Money.new(cents:100) * 125

    @cartNum = 0
    cart.line_items.each do |line_item|
      @cartNum += line_item.quantity
    end

    @hasAllSamples = true
    unless cart.line_items.all? { |line_item| line_item.variant.title.include?("Sample") }
      @hasAllSamples = false
    end

    @hasEuropeanBrand = false
    cart.line_items.each do |line_item|
      if EUROPEAN_BRANDS.include?(line_item.variant.product.vendor)
        @hasEuropeanBrand = true
        break
      end
    end

    @hasMultiBrand = false
    comp_vendor = ""
    cart.line_items.each do |line_item|
      if comp_vendor != "" and line_item.variant.product.vendor != comp_vendor
        @hasMultiBrand = true
        break
      else
        comp_vendor = line_item.variant.product.vendor
      end
    end
  end

  
  def white_glove_shipping(shipping_rates)
    if @isWhileGlove
      # shipping_rates.delete_if { |shipping_rate| shipping_rate.name != 'White Glove Shipping'}
    else
      shipping_rates.delete_if { |shipping_rate| shipping_rate.name == 'White Glove Shipping'}
    end
  end


  def trade_shipping(shipping_rates)
    if @freeShippingEligible
      if @isTrade
        shipping_rates.delete_if do |shipping_rate|
          shipping_rate.name == "Free Shipping"
        end
      else
        shipping_rates.delete_if do |shipping_rate|
          shipping_rate.name.start_with?("UPS® Ground")
        end
      end
    else
      shipping_rates.delete_if do |shipping_rate|
        shipping_rate.name == "Free Shipping"
      end
      shipping_rates.delete_if do |shipping_rate|
          shipping_rate.name.start_with?("UPS® Ground")
      end
    end
  end


  def sample_shipping(shipping_rates)
    if @hasAllSamples
      if @cartNum < 6
        shipping_rates.delete_if do |shipping_rate| 
          shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 1' and shipping_rate.name != 'Overnight Shipping for Samples - 1'
        end
      elsif @cartNum < 11
        shipping_rates.delete_if do |shipping_rate| 
          shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 2' and shipping_rate.name != 'Overnight Shipping for Samples - 2'
        end
      else
        shipping_rates.delete_if do |shipping_rate| 
          shipping_rate.name != 'Free Shipping for Samples' and shipping_rate.name != '2nd Day Shipping for Samples - 3' and shipping_rate.name != 'Overnight Shipping for Samples - 3'
        end
      end
    else
      shipping_rates.delete_if do |shipping_rate|
        shipping_rate.name == 'Free Shipping for Samples' or shipping_rate.name.start_with?('2nd Day Shipping for Samples') or shipping_rate.name.start_with?('Overnight Shipping for Samples')
      end
    end
  end


  def euro_shipping(shipping_rates)
    if @hasEuropeanBrand or @hasMultiBrand
      shipping_rates.delete_if do |shipping_rate| 
        shipping_rate.name.start_with?('UPS 2nd Day') or shipping_rate.name.start_with?('UPS Next Day')
      end
    end
  end
end


shippingRates = UpdateShippingRates.new(Input.cart)
shippingRates.white_glove_shipping(Input.shipping_rates)
shippingRates.trade_shipping(Input.shipping_rates)
shippingRates.sample_shipping(Input.shipping_rates)
shippingRates.euro_shipping(Input.shipping_rates)


Output.shipping_rates = Input.shipping_rates
