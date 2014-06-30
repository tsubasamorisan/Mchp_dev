$(document).ready( function() {
	$('#course_create').bootstrapValidator({
        message: 'This value is not valid',
        feedbackIcons: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        },
        // Set default threshold for all fields. It is null by default
        threshold: 3,
        fields: {
            courseABBR: {
                validators: {
                    notEmpty: {
                        message: 'The course abbreviation is required'
                    },
                    regexp: {
                        regexp: /^[a-zA-Z]+$/i,
                        message: 'The course abbreviation can only consist of alphabetical characters'
                    },
                    stringLength: {
                        min: 3,
                        max: 6,
                        message: 'the course abbreviation should be between 3-6 characters'
                    }
                }
            },
            courseNumber: {
                validators: {
                    notEmpty: {
                        message: 'The course # is required'
                    },
                    regexp: {
                        regexp: /^[a-zA-Z0-9]+$/i,
                        message: 'The course number can only consist of alphabetical characters or numbers'
                    },
                    stringLength: {
                        min: 3,
                        max: 5,
                        message: 'the course number should be between 3-6 characters'
                    }
                }
            },
            courseProf: {
                validators: {
                    notEmpty: {
                        message: 'The course professor\'s last name is required'
                    },
                    regexp: {
                        regexp: /^[a-z]+$/i,
                        message: 'The professor\'s last name can consist of alphabetical characters only with no spaces'
                    },
                    stringLength: {
                        min: 2,
                        max: 20,
                        message: 'the professor\'s last name should be between 2-20 characters'
                    }
                }
            }
        }
    });
});