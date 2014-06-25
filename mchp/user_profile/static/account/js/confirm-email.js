$(function(){
	// to resend verification email
	$("#resend_form").submit(function() {

		// to change resend button state 
		$("#sendBtn").addClass("btn-success");
		$("#sendBtn").html("Verification E-mail sent!");

		var url = "/login/resend-email/"; // page just for handing resend requests

		$.ajax({
			type: "POST",
			url: url,
			data: $("#resend_form").serialize(), 
			dataType: "json",
			success: function(data) {
				$('.resend_confirm').html('<p>Verification Email resent.</p>');
			},
			failure: function(data) {
				alert('Resend request failed.');
			}
		});

		return false; 

	});
	

});
