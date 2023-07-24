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
};


window.pyrengine.articleCheckForm = function() {
	return true;
};


window.pyrengine.editorWrap = function(id, wrap_in)
{
	var f = $('#'+id),
		sel = f.fieldSelection();

	if (sel.length == 0) {
		return;
	}

	var text = wrap_in + sel.text + wrap_in;

	f.fieldSelection(text);
};


window.pyrengine.editorReplace = function(id, text)
{
	var f = $('#'+id),
		sel = f.fieldSelection();

	f.fieldSelection(text);
};


window.pyrengine.editorBlockquote = function(id)
{
	var f = $('#'+id);

	if (f.length == 0) {
		return;
	}

	var sel = f.fieldSelection();

	if (sel.length == 0) {
		return;
	}

	var field_value = f.val(),
		c;

	if (sel.start != 0) {
		// i.e. text starts somewhere in the middle of line
		c = field_value.charCodeAt(sel.start - 1);
		if (c != 10 && c != 13) {
			return;
		}
	}

	var result = [];

	$.each(sel.text.split(/(?:\r\n|\r|\n)/m), function(ind, line) {
		result.push('> ' + line);
	});

	var new_selection = result.join('\n');
	f.fieldSelection(new_selection);
};


window.pyrengine.saveArticle = function(url) {
	var save_button = $('#eid-save-button');
	save_button.attr('disabled', 'disabled');

	var params = {
		title: $('#fid-title').val(),
		shortcut: $('#fid-shortcut').val(),
		published: $('#fid-published').val(),
		tags: $('#fid-tags').val(),
		body: $('#fid-body').val()
	};

	if ($('#fid-is_draft').prop('checked')) {
		params['is_draft'] = 1;
	}
	if ($('#fid-is_commentable').prop('checked')) {
		params['is_commentable'] = 1;
	}

	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(data) {
		if (!data.errors) {
			Pyrone_notify($('#eid-article-notify'), tr('ARTICLE_SAVED'));
		}
		save_button.removeAttr('disabled');
		// return focus back to editing window
		$('#fid-body').focus();
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
		save_button.removeAttr('disabled');
	});
};


window.pyrengine.previewArticle = function() {
	// send AJAX request to the server and display received (and rendered) article body text
	var body = $('#fid-body').val();

	$.ajax({
		url: '/preview/article',
		type: 'POST',
		data: {
			body: body
		}
	}).done(function(data) {
		var e = $('#eid-article-render-preview');
		e.show('slow').html(data);
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};

})();