$(function(){

	// show profile info when friend button clicked (example)
	$('#friend_button').click(function () {
		$('#top_friends').removeClass('hidden');
		$('#top_achievements').removeClass('hidden');
		$('#user_classes').removeClass('hidden');
		$('#friend-message').addClass('hidden');
		$('#shared_classes').addClass('hidden');
	});

	//animating achievement scores
	$('#documentMasterScore').css({'width':'30%', 'transition':'width 2.5s ease 0s'});

	//giving each achievement type a score tooltip 
	$('#documentMasterScore').tooltip({
    'show': true,
        'placement': 'bottom',
        'title': "30%"
	});

	//xeditable options
	$('#about').editable({
    	mode: 'inline',
    	inputclass: 'input-lg',
		url: '/profile/edit-blurb/',
		unsavedclass: 'text-danger',
		emptyclass: '',
		emptytext: 'Add a blurb about yourself here!',
		highlight: '',
		onblur: 'submit',				
		send: 'always',
    });
	var majors = new Bloodhound({
		datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
		queryTokenizer: Bloodhound.tokenizers.whitespace,
		limit: 10,
		prefetch: {
			url: '/school/department/',
			filter: function(list) {
				console.log(list);
				return list;
			}
		}
	});

	$('#major').editable({
		mode: 'inline',
		unsavedclass: 'text-danger',
		emptyclass: '',
		emptytext: 'Select your major',
		highlight: '',
		onblur: 'submit',				
		send: 'always',
		showbuttons: false,
		url: '/profile/edit-major/',
		title: 'Choose your Major',
		typeahead: {
			source: majors.ttAdapter()
		}
	});

	// $('.tt-suggestion > p').selected( function () {
	// 		$(this).addClass('h2');
	// });

	//    value: 'ru',
	// typeahead: {
	// name: 'country',
	// local: [
	// {value: 'ru', tokens: ['Russia']},
	// {value: 'gb', tokens: ['Great Britain']},
	// {value: 'us', tokens: ['United States']}
	// ],
	// template: function(item) {
	// return item.tokens[0] + ' (' + item.value + ')';
	// }
	// }
	// });

	//button to trigger about field (not used right now)
$('#edit-button').click(function(e) {
	e.stopPropagation();
	$('#about').editable('toggle');

});

});
