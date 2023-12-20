# ================================ Customizable Settings ================================
# ================================================================
# Disable Discount Code(s) For Products
#
# If any matching discount codes are used, and any matching items
# are in the cart, the discount code is rejected with the entered
# message.
#
#   - 'discount_code_match_type' determines whether the below
#     strings should be an exact or partial match. Can be:
#       - ':exact' for an exact match
#       - ':partial' for a partial match
#   - 'discount_codes' is a list of strings to identify discount
#     codes
#   - 'product_selector_match_type' determines whether we look for
#     products that do or don't match the entered selectors. Can
#     be:
#       - ':include' to check if the product does match
#       - ':exclude' to make sure the product doesn't match
#   - 'product_selector_type' determines how eligible products
#     will be identified. Can be either:
#       - ':tag' to find products by tag
#       - ':type' to find products by type
#       - ':vendor' to find products by vendor
#       - ':product_id' to find products by ID
#       - ':variant_id' to find products by variant ID
#       - ':subscription' to find subscription products
#       - ':all' for all products
#   - 'product_selectors' is a list of identifiers (from above)
#     for qualifying products. Product/Variant ID lists should
#     only contain numbers (ie. no quotes). If ':all' is used,
#     this can also be 'nil'.
#   - 'rejection_message' is the message to show when a discount
#     code is rejected
# ================================================================
REJECT_DISCOUNT_CODE_FOR_PRODUCTS = [
  {
    discount_code_match_type: :partial,
    discount_codes: ["DBWELCOME1", "QUIZ20", "RAF", "THANKS23", "GIFT23", "HOLIDAY23"],
    customer_tag_match_type: :include,
    customer_tags: ["trade"],
    rejection_message: "Trade members cannot use this code."
  }
]


# ================================ Script Code (do not edit) ================================
# ================================================================
# DiscountCodeSelector
#
# Finds whether the supplied discount code matches any of the
# entered codes.
# ================================================================
class DiscountCodeSelector
  def initialize(match_type, discount_codes)
    @comparator = match_type == :exact ? '==' : 'include?'
    @discount_codes = discount_codes.map { |discount_code| discount_code.upcase.strip }
  end


  def match?(discount_code)
    @discount_codes.any? { |code| discount_code.code.upcase.send(@comparator, code) }
  end
end


# ================================ Script Code (do not edit) ================================
# ================================================================
# CustomerTagSelector
#
# Finds whether the supplied customer has any of the entered tags.
# ================================================================
class CustomerTagSelector
  def initialize(match_type, tags)
    @comparator = match_type == :include ? 'any?' : 'none?'
    @tags = tags.map { |tag| tag.downcase.strip }
  end


  def match?(customer)
    customer_tags = customer.tags.map { |tag| tag.downcase.strip }
    (@tags & customer_tags).send(@comparator)
  end
end


# ================================================================
# DisableDiscountCodesForProductsCampaign
#
# If any matching discount codes are used, and any matching items
# are in the cart, the discount code is rejected with the entered
# message.
# ================================================================
class DisableDiscountCodesForProductsCampaign
  def initialize(campaigns)
    @campaigns = campaigns
  end


  def run(cart)
    return if cart.discount_code.nil?


    @campaigns.each do |campaign|
      customer_tag_selector = CustomerTagSelector.new(campaign[:customer_tag_match_type], campaign[:customer_tags])
      
      discount_code_selector = DiscountCodeSelector.new(
        campaign[:discount_code_match_type],
        campaign[:discount_codes]
      )


      next unless !discount_code_selector.match?(cart.discount_code) && customer_tag_selector.match?(cart.customer)


      cart.discount_code.reject(message: campaign[:rejection_message])
    end
  end
end


# ================================================================
# ApplyFreeSampleLimit
#
# If customer is trade member, he can order up to 10 free samples.
# Remove any free samples from cart if he exceeded the maximum 
# samples. Non-Trade members can't order free samples.
# To-do: Implement auto-replacement with paid samples
# ================================================================
class ApplyFreeSampleLimit
  def initialize(customer)
    if customer.nil? || !customer.tags.include?('trade')
      @free_sample_limit = 0
    else
      @free_sample_limit = 10
    end
  end

  
  def apply(items)
    deleted_items = []
    items.each do |item|
      if item.variant.title.start_with?("Free Sample")
        if @free_sample_limit > 0
          @free_sample_limit -= 1
        else
          deleted_items << item
        end
      end
    end

    deleted_items.each { |item| items.delete(item) }
  end
end


# ================================================================
# ApplyFreeSampleLimit
#
# If customer is trade member, he can order up to 10 free samples.
# Remove any free samples from cart if he exceeded the maximum 
# samples. Non-Trade members can't order free samples.
# To-do: Implement auto-replacement with paid samples
# ================================================================
class ApplySampleOnlyDiscounts
  def initialize(line_items)
    @sample_discount_code = "5FREE"

    @hasAllSamples = true
    unless line_items.all? { |line_item| line_item.variant.title.include?("Sample") }
      @hasAllSamples = false
    end
  end

  def apply(cart)
    return if cart.discount_code.nil?

    if !@hasAllSamples && cart.discount_code.code.upcase == @sample_discount_code
      cart.discount_code.reject(message: "This discount applies exclusively to samples.")
    end

  end
end



if !Input.cart.customer.nil?
  CAMPAIGNS = [
    DisableDiscountCodesForProductsCampaign.new(REJECT_DISCOUNT_CODE_FOR_PRODUCTS),
  ]

  CAMPAIGNS.each do |campaign|
    campaign.run(Input.cart)
  end
end


freeSampleLimit = ApplyFreeSampleLimit.new(Input.cart.customer)
freeSampleLimit.apply(Input.cart.line_items)


sampleOnlyDiscounts = ApplySampleOnlyDiscounts.new(Input.cart.line_items)
sampleOnlyDiscounts.apply(Input.cart)


Output.cart = Input.cart
