/*
 * calendar.js
 *
 * This file handles the functionality of the calendar page.
 */

$(function() {

	/*
	/*
	/* TOUR FUNCTIONS
	/*
	*/
	var stopClearPopovers = clearPopovers();
	var restartClearPopovers = function() {
		stopClearPopovers = clearPopovers();
	};

	// Instance the tour
	// var tour = new Tour({
		
	// 	name: "calendar-tour",
	// 	backdrop: true,
	// 	// storage: false,
	// 	onStart: stopClearPopovers,
	// 	onEnd: restartClearPopovers,
	// 	path: "/calendar/",
	// 	template: "<div class='popover tour'><div class='arrow'></div><h3 class='popover-title'></h3><div class='popover-content'></div><nav class='popover-navigation'><div class='btn-group'><button class='btn btn-default btn-sm' data-role='prev'>« prev</button><button class='btn btn-default btn-sm' data-role='next'>next »</button></div><button class='btn btn-default btn-end btn-sm tour-btn-end' data-role='end'>end tour</button></nav></div>",
	// 	steps: [
	// 	{
	// 		orphan: true,
	// 	    title: "<strong>This is your calendar, " + MCHP_USERNAME + "!</strong>",
	// 	    content: 'You can make a calendar for each of your enrolled classes, with the option to set each one as <strong>public</strong> or <strong>private.</strong>'
	// 	},
	// 	{
	// 		orphan: true,
	// 	    title: "<strong>Private Calendar</strong>",
	// 	    content: "If you want to make it private, only you will be able to see the events you add to it, like a regular calendar."
	// 	},
	// 	{
	// 		orphan: true,
	// 	    title: "<strong>Public Calendar</strong>",
	// 	    content: "If you make it public, your classmates will be able to subscribe to it. In return, they'll get to see the events you add, and get notified whenever you change or add events."
	// 	},
	// 	{
	// 		element: ".owned-cals-section",
	// 	    title: "<strong>Calendars you Own</strong>",
	// 	    content: "The calendars <em>you create</em> will appear here.",
	// 	    placement: "right"
	// 	},
	// 	{
	// 		element: ".following-cals-section",
	// 	    title: "<strong>Calendars you Follow</strong>",
	// 	    content: "The calendars <em>you subscribe to</em> will appear here.",
	// 	    placement: "right",
	// 	     onhide: function() {
	//         	$('.flip-holder').toggleclass("flip");
 //    		}
	// 	},
	// 	{
	// 		element: ".view-cals-btn",
	// 	    title: "<strong>Browse Calendars to Follow</strong>",
	// 	    content: "You can find calendars that your classmates have made here.",
	// 	    placement: "left",
	// 	    reflex: true
	// 	},
	// 	{
	// 		element: "#nav-list",
	// 	    title: "<strong>What\'s next, " + MCHP_USERNAME + "?</strong>",
	// 	    content: "<p>To create a calendar, click <a href='/calendar/create/' id='create-cal-btn'>here.</a> Or, continue exploring...</p>",
	// 	    placement: "bottom",
	// 	    backdrop: false,
	// 	    reflex: true
	// 	}
		
	// ]});

	

	// // initialize the tour
	// tour.init();
	// // start the tour
	// tour.start();
	// // remove backdrop when clicked
	// $('.tour-backdrop').click(function() {
	// 	$(this).remove();
	// });

	



	/************************
	 * for rating calendars *
	 ************************/

	//initialize calendar rating slider
	$('#ex1').slider({
		tooltip: 'drag',
		// selection: 'none',
		natural_arrow_keys: true,
		// formater: function(value) {
		// 	return 'Current value: ' + value;
		// }
	}).on('slideStop', function() {
		var value = $(this).slider('getValue');
		var pk = $(this).data('cal');
		$.ajax({
			url: '/calendar/subscription/update/',
			type: 'POST',
			data: {
				'calendar': pk,
				'rating': value,
			},
			success: function(data) {
				// update the rating information 
				$('#rate-link-' + pk).data('rating', value);
			},
			fail: function(data) {
			},
			complete: function(data) {
			},
		});
	});
	$('#rate-cal-modal').on('show.bs.modal', function() {
		var $modal = $(this);
		var $slider = $('#ex1');
		$slider.data('cal', $modal.data('cal'));
	});

	/*******************************
	 * FOR EDITING CALENDAR EVENTS *
	 *******************************/
	var editableError = function(data) {
		$('.editable-success').text('');
		$('.editable-errors').text(data.responseJSON.response).fadeIn(500).delay(1000).fadeOut(500);
	};
	$.fn.editable.defaults.error = editableError;
	var editableSuccess = function(data) {
		if(data.hasOwnProperty('privacy') && data.privacy === true) {
			$('.calendar-privacy-field').toggleClass('hidden');
		}
		$('.editable-errors').text('');
		$('.editable-success').text(data.response).fadeIn(500).delay(1000).fadeOut(500);
		$('#calendar').fullCalendar('refetchEvents');
	};
	$.fn.editable.defaults.success = editableSuccess;

	// make title editable
	var eventEditUrl = '/calendar/events/update/';
	$('.edit-event-title').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: eventEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Enter an Event Title',
			highlight: '',
			onblur: 'submit',
			send: 'always',
	});
	// initialize date picker
	// this is duplicated code from below but I needed it to work
	// -mitch
	$('input.date').datepicker({
		format: "D M d, yyyy", //"yyyy-m-d"
	    startDate: "today",
		autoclose: true,
    }).on('changeDate', function(jsEvent) {
		var pick = moment.utc(jsEvent.date);

		var $modal = $('#event-edit-modal');
		var events = $modal.data('events');
		var pk = $modal.data('event-id');
		var event = null;
		$.each(events, function(index, e) {
			if(e.id == pk) {
				event = e;
			}
		});

		var $editable = $('.date-holder');
		date_string = 'ddd MMM DD, YYYY';
		$editable.editable('option', 'value', pick.format(date_string));

		var time = moment.utc(event.start);
		pick.hour(time.hour());
		pick.minute(time.minute());

		$editable.editable('option', 'pk', pk);
		$editable.editable('submit', {
			url: eventEditUrl,
			data: {
				pk: pk, 
				date: JSON.stringify(pick),
			},
			success: editableSuccess,
			error: editableError,
		});
	});

	// changing the date
	$('.edit-event-date').editable({
	    	mode: 'inline',
	    	inputclass: '',
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Enter a date',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
	});
	// picking the time
	$('.edit-event-time').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: eventEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Enter a time',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
	});
    // initializing clockpicker
	$('.clockpicker').clockpicker( {
		twelvehour: 'true',
		afterDone: function() {
			var $modal = $('#event-edit-modal');
			var events = $modal.data('events');
			var pk = $modal.data('event-id');
			var event = null;
			$.each(events, function(index, e) {
				if(e.id == pk) {
					event = e;
				}
			});

			var $editable = $('.time-holder');
			$editable.editable('option', 'value', $('.time-input').val());

			var time = moment.utc($('.time-input').val(), 'hh:mmA');
			var date = moment.utc(event.start);
			date.hour(time.hour());
			date.minute(time.minute());

			$editable.editable('option', 'pk', pk);
			$editable.editable('submit', {
				url: eventEditUrl,
				data: {
					pk: pk, 
					date: JSON.stringify(date),
				},
				success: editableSuccess,
				error: editableError,
				pk: pk,
			});
		}
	});
	// make the class editable
	$('.edit-event-class').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: eventEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Pick class',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
			value: -1,
			autotext: 'auto',
	});
	// replacing the description with notes
	$('.edit-event-description').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: eventEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'description',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
			rows: 3,
	});


	/**************************
	 * FOR MANAGING CALENDARS *
	 **************************/
	$('.manage-calendar-tab').click(function(){
		$('.manage-calendar-tab').removeClass('active');
		$('.prompt-delete-message').addClass('hidden');
		$('.not-delete-button').addClass('hidden');
		$('.confirm-delete-button').addClass('hidden');
		$('.end-subscription').addClass('hidden');
		$('.prompt-delete-button').removeClass('hidden');

	});

	$('.prompt-delete-button').on('click', function () {
		$(this).addClass('hidden');
		$('.prompt-delete-message').removeClass('hidden');
		$('.not-delete-button').removeClass('hidden');
		$('.confirm-delete-button').removeClass('hidden');
		$('.end-subscription').removeClass('hidden');
	});

	$('.not-delete-button').on('click', function () {
		$('.prompt-delete-button').removeClass('hidden');
		$('.prompt-delete-message').addClass('hidden');
		$('.not-delete-button').addClass('hidden');
		$('.confirm-delete-button').addClass('hidden');
		$('.end-subscription').addClass('hidden');
	});

	$('.confirm-delete-button').on('click', function () {
		$('.prompt-delete-message').addClass('hidden');
		$('.not-delete-button').addClass('hidden');
		$('.confirm-delete-button').addClass('hidden');
		$('.end-subscription').addClass('hidden');
	});

	var calendarEditUrl = '/calendar/update/';
	// make the class editable
	$('.calendar-selling').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: calendarEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
			source: [
				{value: 1, text: 'Yes'},
				{value: 2, text: 'No'},
			]
	});

	// for the calendar description
	$('.calendar-description').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: calendarEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Provide a description for your calendar',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
	});

	// for the calendar date
	$('.edit-calendar-date').editable({
	    	mode: 'inline',
	    	inputclass: '',
			url: calendarEditUrl,
			unsavedclass: 'text-danger',
			emptyclass: '',
			emptytext: 'Enter an end date',
			highlight: '',
			onblur: 'submit',				
			send: 'always',
	});

	$('.calendar-date').datepicker({
		format: "D M d, yyyy", //"yyyy-m-d"
	    startDate: "today",
		autoclose: true,
    }).on('changeDate', function(jsEvent) {
		var pick = moment.utc(jsEvent.date);
		pick.hour(23);
		pick.minute(59);

		var pk = $(this).data('pk');

		var $editable = $('.calendar-date-holder');
		date_string = 'ddd MMM DD, YYYY';
		$editable.editable('option', 'value', pick.format(date_string));

		$editable.editable('option', 'pk', pk);
		$editable.editable('submit', {
			url: calendarEditUrl,
			data: {
				pk: pk, 
				date: JSON.stringify(pick),
			},
			success: editableSuccess,
			error: editableError,
		});
	});

	// when the modal pops up, fill in the right info
	// this modal gets it events when a event hover popover is created
	// and it gets the pk from the link that was clicked to open it
	$('#event-edit-modal').on('show.bs.modal', function() {
		var $modal = $('#event-edit-modal');
		var events = $modal.data('events');
		var pk = $modal.data('event-id');
		var event = null;
		$.each(events, function(index, e) {
			if(e.id == pk) {
				event = e;
			}
		});
		// give the modal the event specific information
		date_string = 'ddd MMM DD, YYYY';
		$modal.find('.edit-event-title').editable('option', 'value', event.title);
		$modal.find('.edit-event-title').editable('option', 'pk', event.id);
		$modal.find('.edit-event-title').editable('option', 'name', 'title');

		$modal.find('.edit-event-date').editable('option', 'value', event.start.format(date_string));
		$modal.find('.edit-event-date').editable('option', 'pk', event.id);
		$modal.find('.edit-event-date').editable('option', 'name', 'date');

		$modal.find('.edit-event-time').editable('option', 'value', event.start.format('hh:mm a'));
		$modal.find('.edit-event-time').editable('option', 'pk', event.id);
		$modal.find('.edit-event-time').editable('option', 'name', 'time');

		$modal.find('.edit-event-class').editable('option', 'emptytext', event.course);
		$modal.find('.edit-event-class').editable('option', 'pk', event.id);
		$modal.find('.edit-event-class').editable('option', 'value', event.course_pk);
		$modal.find('.edit-event-class').editable('option', 'name', 'class');
		$modal.find('.edit-event-class').editable('option', 'source', calendarCourses);

		$modal.find('.edit-event-description').editable('option', 'value', event.description);
		$modal.find('.edit-event-description').editable('option', 'pk', event.id);
		$modal.find('.edit-event-description').editable('option', 'name', 'description');

		$modal.find('.control-label').css('color', event.color);
	});

	/**
	 * End a subscription
	 **/
	$('.end-subscription').click(function() {
		endSubscription($(this).data('cal'));
		$('#subscription-label-holder-'+$(this).data('cal')).remove();
	});

	// using jquery.cookie plugin
	var csrftoken = $.cookie('csrftoken');
	function csrfSafeMethod(method) {
		// these HTTP methods do not require CSRF protection
		return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}
	// csrf token stuff
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});

	$('.confirm-delete-button').click(function() {

		var pk = $(this).data('cal');
		deleteCalendar(pk);
		// remove from cal list
		var $link_parent = $('#owned-calendar-holder-'+pk);
		$link_parent.fadeOut(500, function() {
			$link_parent.remove();
			var count = parseInt($('#owned-calendar-count').text()) - 1;
			$('#owned-calendar-count').text(count);
			if (count < 1) {
				$('#make-a-calendar').removeClass('hidden');
			}
		});
		// remove from manage modal
		var modal = $('#manage-calendars');
		modal.find('#edit-calendar-link-'+pk).remove();
		modal.find('#edit-calendar-tab-'+pk).remove();
	});

	$('.toggle-events').click(function(jsEvent) {
		var pk = $(this).data('cal');
		updateEvents(pk);
	});

	/**********************
	 * FULLCALENDAR STUFF *
	 **********************/

	var today = new Date().toJSON().slice(0,10);
	$('#calendar').fullCalendar({
		header: false,
    	weekMode: 'liquid',

		//trigger add event pop-up on click and stay
		dayClick: function(date, jsEvent, view) {
			if(!$('.owned-calendar-holder').length){
				return;
			}
			// remove the other popovers
			$('.popover').remove();
			// show the clicked day popover
			date_string = date.format('ddd MMM DD, YYYY');
			$('.date-input').data('date', date);
			$('.date-input').attr('value', date_string);

			$(this).popover({
				trigger: 'manual',
				placement: 'auto',
				html: true,
				viewport: 'body',
				title: function() {
					return $('#popover-title').html();
				},
				content: function() {
					return $('#popover-content').html();
				},
				container: 'body',
			});
			$(this).popover('show');

			var $target = $(jsEvent.target);
			var startDate = $target.data('date');
			startDate = moment.utc(startDate);
			$('input[name=title]').focus();

			// initialize date picker
			$('input.date').datepicker({
				format: "D M d, yyyy", 
				startDate: 'today',
				autoclose: true,
			}).on('changeDate', function(event) {
				var date = event.date;
				var pick = moment.utc(date);
				$('.date-input').data('date', pick);
			});
		},

		events: {
			url: '/calendar/feed/',
			type: 'GET',
			success: function(data) {
				var events = [];
				$.each(data.events, function(index, event) {
					events.push({
						'start': moment.utc(event.start),
						'end': moment.utc(event.end),
						'id': event.id,
						'title': event.title,
						'description': event.description,
						'course': event.course,
						'color': event.calendar__color,
						'course_pk': event.calendar__course__pk,
						'calendar': event.calendar__pk,
						'visible': true,
						'private': event.calendar__private,
						'owned': event.owned,
						'last_edit': moment.utc(event.last_edit),
						'author': event.author || '',
						'authorPK': event.author_pk || -1,
					});
				});
				$('.fc-day').each(function() {
					// remove any old events
					$(this).data('events', []);
					// Get current day
					var day = moment.utc($(this).data('date'));
					// if this day has an event
					var event_count = 0;
					while(events.length && events[0].start.diff(day, 'days')===0) {
						event_count++;
						// this work because the events are sorted, and we only ever take the first
						// one from the array
						var event = events.shift();
						var $day = $(this);
						if ($day.data('events')) {
							$day.data('events').push(event);
						} else {
							$day.data('events', [event]);
						}
					}
					// draw a number w/ num of events for that day
					drawEvents($(this), event_count);
				});
			},
			error: function() {
				addMessage('Error getting events', 'danger');
			},
		},
		eventRender: function(event, element) {
			// don't show the fullcalendar events
			return false;
		},
		eventAfterAllRender: function(view) {
		},
		timezone: 'local',
	});

	/*****************
	 * popover stuff *
	 *****************/
	$('#calendar').on('mouseenter', '.canvas-day', function(jsEvent) {
		$(this).popover('destroy');
		$(this).popover({
			trigger: "focus",
			placement: 'auto',
			html: true,
			content: function() {
				var $fcDay = $(this).parents('.fc-day');
				var $event_list = $('#events-popover-content').clone();
				var $item_proto = $event_list.find('.list-group-item').clone();
				$event_list.find('.list-group-item').remove();
				var $list_group = $event_list.find('.list-group');
				var format_string = 'ddd MMM DD, YYYY';
				$.each($fcDay.data('events'), function(index, event) {
					// skip events that have been hidden
					if(!event.visible) {
						return true;
					}
					var $item = $item_proto.clone();
					$item.find('.event-title').text(event.title).attr('href', '/calendar/events/' + event.id);
					$item.find('.event-description').text(event.description);
					$item.find('.event-date').text(event.start.format(format_string));
					$item.find('.event-time').text(event.start.format('hh:mm a'));
					$item.find('.event-class').text(event.course);
					$item.find('.event-id').text(event.id);
					$item.find('.event-author-link').text(event.author);
					$item.find('.event-author-link').attr('href', '/profile/'+ event.authorPK);
					$item.find('.calendar-indicator').css('color', event.color);
					if(event.private) {
						$item.find('.fa-bullhorn').remove();
					}
					if(!event.owned) {
						$item.find('.event-edit-link').remove();
						$item.find('.event-delete-link').remove();
						$item.find('.fa-bullhorn').remove();
					} else {
						$item.find('.event-author').remove();
					}
					$list_group.append($item);
				});
				// add event for new edit cal button
				// this is how the modal gets events in it
				var $modal = $('#event-edit-modal');
				$modal.data('events', $fcDay.data('events'));

				return $event_list.html();
			},
			container: 'body',
		});
		$('.popover').remove();
		$(this).popover('show');

		$('.event-edit-link').click(function() {
			var pk = $(this).parents('.list-group-item').children('.event-id').text();
			var $modal = $('#event-edit-modal');
			$modal.data('event-id', pk);
			$modal.modal('show');
		});
		$('.event-delete-link').click(function() {
			var pk = $(this).parents('.list-group-item').children('.event-id').text();
			$.ajax({
				url: '/calendar/events/delete/',
				type: 'POST',
				data: {'pk': pk},
				success: function(data) {
					messages = data.messages;
					// refresh calendar
					$cal = $('#calendar');
					$cal.fullCalendar('refetchEvents');
				},
				fail: function(data) {
					addMessage('Failed to delete event', 'danger');
				},
				complete: function(data) {
					$.each(messages, function(index, message){
						addMessage(message.message, message.extra_tags);
					});
				},
			});
			$(this).parents('.list-group-item').remove();
		});
	});
	$('#calendar').on('mouseleave', '.canvas-day', function(jsEvent) {
		var $canvas = $(this);
		setTimeout(function () {
			if(!$('.popover:hover').length) {
				$canvas.popover('hide');
			}
		}, 100);
	});

	// click on date w/ events on it
	$('#calendar').on('click', '.canvas-day', function(event) {
		if(!$('.owned-calendar-holder').length){
			return;
		}
		// why? why does this one need a stop propagation, and the mouseover will break if you do
		// that. seriously, wtf
		event.stopPropagation();
		$(this).popover('destroy');
		$('.popover').remove();
		$(this).popover({
			trigger: 'manual',
			placement: 'auto',
			html: true,
			viewport: '',
			title: function() {
				return $('#popover-title').html();
			},
			content: function() {
				return $('#popover-content').html();
			},
			container: 'body',
		});
		$(this).popover('show');
		$('input[name=title]').focus();

		// initialize date picker
		$('input.date').datepicker({
			format: "D M d, yyyy", 
			startDate: 'today',
		}).on('changeDate', function(event) {
			var date = event.date;
			var pick = moment.utc(date);
			$('.date-input').data('date', pick);
		});
	});

	// close the popovers when you click outside
	// this is add to the body so it can be registered
	// with dynamically added popovers
	$('body').on('click', function (event) {
		var $target = $(event.target);
		// this makes baby pandas around the world cry salty tears
		if(!($target.hasClass('btn') ||
				 $target.hasClass('day') ||
				 $target.hasClass('date') ||
				 $target.hasClass('fc-day') ||
				 $target.hasClass('popover-title') ||
				 $target.hasClass('popover-content') ||
				 $target.hasClass('datepicker-switch') ||
				 $target.hasClass('datepicker-days') ||
				 $target.hasClass('table-condensed') ||
				 $target.hasClass('prev') ||
				 $target.hasClass('next') ||
				 $target.hasClass('dow') ||
				 $target.is('span') ||
				 $target.is('a') ||
				 $target.hasClass('form-control')
				)) {
			$('.popover').popover('hide');
		}
		// when you click on any of the list items in the drop down
    	$("#calSelect > li a").click(function(){
			// replace the cal icon with the title of the calendar
	        $(".cal-name").html($(this).clone());
	        $(".cal-name").data('calendar', $(this).data('calendar'));
    	});
	});

	// submitting the form in the event creation popover
	$('body').on('submit', '#add-event-form', function(event) {
		var $form = $(event.target);
		var url = '/calendar/events/add/';
		var messages = [];
		data = '';

		// which calendar this event is for 
		var cal = $('.cal-name').data('calendar');
		data += "calendar=" + encodeURIComponent(cal);

		var date = $('.date-input').data('date');
		events = {};
		var title = $form.find('input[name=title]').val();
		var description = $form.find('input[name=description]').val();
		// don't bother sending empty entries
		// make a new event
		var newEvent = {
			'title': title,
			'description': description,
			'date': date.toJSON(),
			'hasTime': false,
		};
		events[0] = newEvent;
		events = JSON.stringify(events);
		data += "&events=" + encodeURIComponent(events);

		$.ajax({
			url: url,
			type: 'POST',
			data: data,
			success: function(data) {
				messages = data.messages;
				// add the event to the calendar
				$cal = $('#calendar');
				$cal.fullCalendar('refetchEvents');
			},
			fail: function(data) {
				addMessage('Failed to save event', 'danger');
			},
			complete: function(data) {
				$.each(messages, function(index, message){
					addMessage(message.message, message.extra_tags);
				});
			},

		});
		$('.popover').popover('hide');
		return false;
	});

	/*********************************
	 * CUSTOM HEADER BUTTONS FOR CAL *
	 *********************************/
	//	custom date above calendar 
	$('.cal-date').html(function () {
		var view = $('#calendar').fullCalendar('getView');
		return view.title;
	});

	// today button
	$('.cal-today-button').click(function() {
    	$('#calendar').fullCalendar('today');
	});

	// prev button
	$('.cal-prev-button').click(function() {
    	$('#calendar').fullCalendar('prev');
	});
	// next button
	$('.cal-next-button').click(function() {
    	$('#calendar').fullCalendar('next');
	});

	// change the title when the view changes
	$('.cal-button').click(function() {
    	$('.cal-date').text(function () {
			var view = $('#calendar').fullCalendar('getView');
			return view.title;
		});
	});

	//toggle calendar list section
    $('.view-cals').on('click', function () {
        $('.flip-holder').toggleClass("flip");
		$('.calendar-list-toggle.active').click();
		$('.popover').remove();
		$('.modal').remove();
    });
	$('.calendar-list-toggle').click(function() {
		var $toggleLink = $(this);
		var fetched = $toggleLink.data('fetched');
		if(fetched === true) {
			return;
		}
		var course = $toggleLink.data('course');
		var $calTab = $('#browse-tab-'+course);

		var messages = [];
		$.ajax({
			url: '/calendar/list/',
			type: 'GET',
			data: {
				'course': course,
			},
			dataType: 'json',
			success: function(data) {
				var $calList =  $calTab.find('.calendar-item-list');
				$('#calendar-count-'+course).text(data.calendars.length);

				if(data.hasOwnProperty('calendars') && data.calendars.length > 0) {
					var subscriptions = $('.subscription-list').map(function(index, element){
						return $(element).find('label').data('cal');
					}).get();
					$.each(data.calendars, function(index, calendar) {
						var $calendar = $calList.find('.calendar-item-proto').clone();
						$calendar.removeClass('hidden');
						$calendar.removeClass('calendar-item-proto');
						$calendar.find('.calendar-title').text(calendar.title);
						$calendar.find('.calendar-title').attr('href', '/calendar/preview/'+calendar.pk);
						$calendar.find('.calendar-picture-link').attr('href', '/calendar/preview/'+calendar.pk);
						$calendar.find('.calendar-uploader').attr('href', '/profile/'+calendar.owner);
						$calendar.find('.calendar-uploader').text(calendar.owner__user__username);
						$calendar.find('.calendar-description').text(calendar.description);
						$calendar.find('.calendar-subscriptions').text(' ' + calendar.subscriptions + ' followers');
						$calendar.find('.calendar-event-count').text(calendar.events);
						$calendar.find('.calendar-create-date').text(moment.utc(calendar.date).from(moment.utc()));
						$calendar.find('.calendar-professor').text(calendar.course__professor);
						$calendar.find('.calendar-time').html(calendar.time);
						$calList.append($calendar);
					});
				} else {
					$calList.html('<hr><p class="lead">There are no calendars for this course yet. That means no competition for you. <a href="/calendar/create">Create the first Calendar</a> for your classmates to follow and make some money! </p><hr>');
				}
				$toggleLink.data('fetched', true);
			},
			fail: function(data) {
			},
			complete: function(data) {
				$.each(messages, function(index, message){
					addMessage(message.message, message.extra_tags);
				});
			},
		});
	});

});

var endSubscription = function(cal_pk) {
	var messages = [];
	$.ajax({
		url: '/calendar/unsubscribe/',
		type: 'POST',
		data: {
			'pk': cal_pk,
		},
		dataType: 'json',
		success: function(data) {
			messages = data.messages;
		},
		fail: function(data) {
			messages = data.responseJSON.messages;
		},
		complete: function(data) {
			$.each(messages, function(index, message){
				addMessage(message.message, message.extra_tags);
			});
		},
	});
};
var deleteCalendar = function(cal_pk) {
	var messages = [];
	$.ajax({
		url: '/calendar/delete/',
		type: 'POST',
		data: {
			'id': cal_pk,
		},
		dataType: 'json',
		success: function(data) {
		},
		fail: function(data) {
		},
		complete: function(data) {
			messages = data.responseJSON.messages;
			$.each(messages, function(index, message){
				addMessage(message.message, message.extra_tags);
			});
		},
	});
};
var drawCircle = function(canvas, old) {
	var count = $(canvas).data('count');

	if (canvas.getContext){
		var ctx = canvas.getContext('2d');
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		ctx.beginPath();
		var x              = $(canvas).width() / 2;               // x coordinate
		var y              = $(canvas).height() / 2;              // y coordinate
		var radius         = $(canvas).width() / 4.5;             // Arc radius
		var startAngle     = 0;                     							// Starting point on circle
		var endAngle       = Math.PI * 2; 												// End point on circle
		var anticlockwise  = true; 																// clockwise or anticlockwise

		ctx.arc(x, y, radius, startAngle, endAngle, anticlockwise);

		var color = "rgba(255,255,255,0.4)";
		var stroke = "#FFFFFF";
		if (old) {
			ctx.globalAlpha = 0.4;
			stroke = 'rgba(0,0,0,0)';
		}

		ctx.fillStyle=color;
		ctx.fill();
		ctx.fillStyle="#FFFFFF";
      	ctx.lineWidth = 1;
		ctx.strokeStyle = stroke;
      	ctx.stroke();

		var font_x = parseInt(y*(2/3)).toString();
		ctx.font = font_x  + "pt Helvetica";
		var text_start = ctx.measureText(count);
		ctx.fillText(count, x-text_start.width/2, y + (y*(2/7)));
  }
};

var TODAY = moment().startOf('day').utc().startOf('day');

var drawEvents = function(day, count){
	// first remove old count
	day.find('.canvas-day').remove();

	// don't show any 0 event days
	if (count < 1) {
		return;
	}
	// date for this calendar day
	var date = moment.utc(day.data('date'));
	// create a new canvas element the size of the cal day
	var $canvas = $('<canvas id="canvas-'+
			date.format('YYYY-M-DD') +
			'" class="'+ 
			"canvas-day text-center center-block" + 
			'" height="'+ 
			(day.height()-13)+
			'" width="'+
			day.width()+
			'" data-count="'+
			count+
			'"></canvas>');
	day.html($canvas);
	var old = false;
	if (date.isBefore(TODAY)) {
		old = true;
	}
	drawCircle($canvas.get(0), old);
};

var updateEvents = function(calendar) {
	$('.popover').remove();
	$('.fc-day').each(function() {
		var day = moment.utc($(this).data('date'));
		// get events for this day
		var events = $(this).data('events');
		// there are no events for this day
		if (typeof events === 'undefined' ){
			return true;
		}
		eventCount = 0;
		// toggle events 
		$.each(events, function(index, event) {
			if(calendar === event.calendar) {
				event.visible = !event.visible;
			}
			if(event.visible) {
				eventCount++;
			}
		});

		// draw a number w/ num of events for that day
		drawEvents($(this), eventCount);
	});
};

var CLEAR_TIME = 1000;
var clearPopovers = function () {
	function run() {
		if(!$('.popover:hover').length && !$('.canvas-day:hover').length && !$('.fc-day:hover').length) {
			$('.event-popover-container').each(function() {
				var pop = $(this).parent().parent('.popover');
				pop.remove();
			});
		}
		timer = setTimeout(run, CLEAR_TIME);
	}
	timer = setTimeout(run, CLEAR_TIME);

	function stop() {
		if (timer) {
			clearTimeout(timer);
			timer = 0;
		}
	}
	return stop;
};
