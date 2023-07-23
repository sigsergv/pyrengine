(function() {

window.pyrengine = {};

window.pyrengine.logout = function() {
	$.ajax({
		url: '/logout',
		type: 'POST'
	}).done(function(){
		window.location.replace('/');
	}).fail(function() {
		alert(_tr('AJAX_REQUEST_ERROR'));
	});
}

})();