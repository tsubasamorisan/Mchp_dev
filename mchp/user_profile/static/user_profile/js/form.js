//Signup form show/hide
$(function () {
	// show manual sign up forms
	$('#show-signUp').on('click', function () {
		$('.facebookSignup').fadeOut(250, function () {
			$('.emailSignup').fadeIn(500);
			$('.email_reminder').fadeIn(500);
		});
	});
	// show manual log in forms
	$('#show-login').on('click', function () {
		$('#facebookLogin').fadeOut(250, function () {
			$('.emailLogin').fadeIn(500);
		});
	});

	// this is to add the session stored email address, and hide that field
	$('.email_reminder').hide();
	hidden = $('.signup input[name=saved_email]').attr('value');
	if(hidden !== ''){
		$('#id_email').hide();
		$('label[for=id_email]').hide();
		$('#id_email').attr('value', $hidden);
	} else if(hidden === '') {
		// if there is no session email, this will show the e-mail input field
		$('.email_reminder h4').html("Sign up with E-mail")
	}
});