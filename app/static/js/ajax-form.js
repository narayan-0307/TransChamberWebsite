$(function () {
	// Get the form.
	var form = $('#contact-form');

	// Get the messages div.
	var formMessages = $('.ajax-response');

	// Optional: Add some basic form validation
	$(form).submit(function (e) {

		var name = $('input[name="name"]').val().trim();
		var email = $('input[name="email"]').val().trim();
		var purpose = $('select[name="purpose"]').val();

		if (!name || !email || !purpose) {
			alert('Please fill in all required fields.');
			e.preventDefault();
			return false;
		}

		// Basic email validation
		if (!email.includes('@') || !email.includes('.')) {
			alert('Please enter a valid email address.');
			e.preventDefault();
			return false;
		}

		// Show loading message
		$(formMessages).removeClass('error success');
		$(formMessages).addClass('info');
		$(formMessages).text('Submitting your message...');
		return true; // Allow form to submit normally
	});
});
