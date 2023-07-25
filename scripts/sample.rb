free_sample_limit = 10
customer = Input.cart.customer

already_ordered_free_samples = Order.completed
                                .joins(line_items: :variant)
                                .where(customer: customer)
                                .where("line_items.created_at > ? AND variants.title LIKE ?", 24.hours.ago, "%Free Sample%")
                                .sum('line_items.quantity')

remaining_free_samples = free_sample_limit - already_ordered_free_samples

Input.cart.line_items.each do |item|
    if item.variant.name.start_with?("Free Sample")
        if remaining_free_samples > 0
            remaining_free_samples -= 1
        else
            Input.cart.line_items.delete(item)
            
            product = item.variant.product
            paid_sample = product.variants.find { |variant| variant.title.start_with?("Sample") }
            
            Input.cart.line_items << paid_sample
        end
    end
end

Output.cart = Input.cart