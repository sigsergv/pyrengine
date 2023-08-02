(function() {

var tr = function(s) {
    if (translations[s]) {
        return translations[s];
    }
    return s;
};

window.pyrengine = {};

/**
 * Update element text, show it and then hide after timeout
 */
var pyrengine_notify = function(elem, text, afterfunc, timeout) {
	if (!timeout) {
		timeout = 3000;
	}
	elem.html(text);
	elem.slideDown(300).delay(timeout).slideUp(300);
};

var pyrengine_field_error = function(field, msg) {
	if (msg === null) {
		$('#error-'+field).html('').hide(0);
	} else {
		$('#error-'+field).html(msg).show(0);
	}
};

var pyrengine_get_selected_rows = function(table_id) {
	var table = $('#'+table_id);
	if (!table.get(0)) {
		return false;
	}
	
	var nodes = table.find('input[class=list-cb]'),
		res = [];

	nodes.each(function(ind, el) {
		if (el.checked) {
			res.push(el.value);
		}
	});
	return res;
};

var pyrengine_create_link_notify_box = function(target_id, message) {
	var notify_id = 'notifybox-' + target_id;
	if ($('#'+notify_id).get(0)) {
		return;
	}
	var target = $('#'+target_id);
	if (!target.get(0)) {
		return;
	}

	var notify_el = $('<SPAN></SPAN>').attr({
		href: '#',
		id: notify_id
	}).text(message).addClass('notify-icon')
	  .click(function(e) {
	  	  notify_el.remove();
	  	  return false;
	  });
	target.after(notify_el);

	setTimeout(function(){
		notify_el.remove();
	}, 1000);
};

/**
 * @param {String} target_id id of node where append confirm box
 * @param {Function} callback required callback to be called when user clicks confirm box
 */
 var create_confirm_link = function(target_id, callback) {
	var confirm_id = 'confirmlink-' + target_id;
	if ($('#'+confirm_id).get(0)) {
		return;
	}

	var target = document.getElementById(target_id);
	if (!target) {
		return;
	}
	target = $(target);

	var confirmation_el = $('<a> <span class="fa fa-check-circle"> OK</a>').attr({
		href: '#',
		id: confirm_id
	}).addClass('confirm-icon')
	  .click(function(e) {
	  	  callback.call();
	  	  confirmation_el.remove();
	  	  return false;
	  });
	target.after(confirmation_el);

	setTimeout(function(){
		confirmation_el.remove();
	}, 1000);
}


window.pyrengine.logout = function() {
	$.ajax({
		url: '/logout',
		type: 'POST'
	}).done(function(){
		window.location.replace('/');
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};


window.pyrengine.selectDeselectAll = function(table_id)
{
	var table = $('#'+table_id);
	if (!table.get(0)) {
		return false;
	}

	var nodes = table.find('input[class=list-cb]').filter('[disabled!=disabled]'),
		checked_count = 0,
		not_checked_count = 0;

	nodes.each(function(ind, el) {
		if (el.checked) {
			checked_count++;
		} else {
			not_checked_count++;
		}
	});

	var new_state;

	if (checked_count > 0 && not_checked_count == 0) {
		// i.e. all rows selected, so clear selection
		new_state = false;
	} else {
		// select all otherwise
		new_state = true;
	}
	nodes.prop('checked', new_state);
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

	pyrengine_field_error('body', null);
	pyrengine_field_error('title', null);
	pyrengine_field_error('shortcut', null);
	pyrengine_field_error('published', null);

	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(data) {
		if (data.success) {
			pyrengine_notify($('#eid-article-notify'), tr('ARTICLE_SAVED'));
		} else {
			pyrengine_notify($('#eid-article-warning'), tr('ARTICLE_SAVE_FAILED'));
			var error_messages = {};
			$.each(data.errors, function(ind, e) {
				var field = e[0],
					msg = e[1];
				if (!error_messages[field]) {
					error_messages[field] = [];
				}
				error_messages[field].push(msg)
			});
		}
		for (field in error_messages) {
			pyrengine_field_error(field, error_messages[field].join('<br>'))
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
		url: '/article/preview',
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


window.pyrengine.replyToArticleComment = function(comment_id) {
	var comment_block = $('#c-'+comment_id),
		comment_form = $('#eid-comment-form'),
		link = $('#eid-leave-comment-link-bottom'),
		parent_comment_field = $('#fid-parent-comment');
	
	if (!comment_block.get(0)) {
		return;
	}
	comment_block.append(comment_form);
	
	if (comment_id === -1) {
		link.hide(0);
		parent_comment_field.val('');
	} else {
		parent_comment_field.val(comment_id);
		link.show(0);
	}
	$('#fid-comment-body').focus();
};


window.pyrengine.submitArticleCommentEditForm = function(url_template) {
	var comment_id = $('#c-edit-comment_id').val();
	
	if (comment_id == '') {
		return;
	}
	
	var submit_url = url_template.replace(/666/, comment_id),
		params = {},
		fields = ['body', 'name', 'email', 'website', 'date', 'ip', 'xffip'];
	
	$.each(fields, function(ind, fn) {
		params[fn] = $('#c-edit-'+fn).val();
	});
	
	if ($('#c-edit-is_subscribed').prop('checked')) {
		params['is_subscribed'] = 'true';
	}
	
	$.ajax({
		url: submit_url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(json) {
		inner = $('#c-inner-'+comment_id),
		edit_form = $('#c-edit');
	
		edit_form.hide(0);
		inner.show(0);
		
		// re-render comment
		if (json.rendered) {
			inner.html(json.rendered);
		}
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};


window.pyrengine.cancelArticleCommentEditForm = function() {
	var comment_id = $('#c-edit-comment_id').val(),
		inner = $('#c-inner-'+comment_id),
		edit_form = $('#c-edit');
	
	edit_form.hide(0);
	inner.show(0);
};


window.pyrengine.postArticleComment = function() {
	var body = $('#fid-comment-body').val();
	var e = $('#eid-comment-error');
	
	if (body == '') {
		var body_el = $('#fid-comment-body');
		body_el.focus();
		pyrengine_notify(e, tr('COMMENT_BODY_IS_REQUIRED'));
		return;
	}
	
	var f = $('#eid-comment-form'),
		url = f.prop('action') + '/ajax',
		article_id = $('#fid-article_id').val(),
		parent = $('#fid-parent-comment').val(),
		display_name = $('#fid-comment-displayname').val(),
		email = $('#fid-comment-email').val(),
		website = $('#fid-comment-website').val(),
		is_subscribed = $('#fid-is_subscribed').prop('checked');
	
	var params = {s: article_id};
	params[article_id.substring(3, 14)] = body;
	params[article_id.substring(4, 12)] = parent;
	params[article_id.substring(0, 5)] = display_name;
	params[article_id.substring(13, 25)] = email;
	params[article_id.substring(15, 21)] = website;
	console.log('is_subscribed', is_subscribed);
	if (is_subscribed === true) {
		params[article_id.substring(19, 27)] = 'true';
	}
	
	var display_name_field = $('#fid-comment-displayname');
	
	if (display_name_field.prop('type') == 'text' && display_name == '') {
		display_name_field.focus();
		pyrengine_notify(e, tr('COMMENT_DISPLAY_NAME_IS_REQUIRED'));
		return;
	}
	
	var disable_ids = ['fid-comment-displayname', 'fid-comment-email', 'fid-comment-website',
		'fid-comment-body', 'eid-post-comment-button', 'fid-is_subscribed'];

	function setFieldsDisabled(disable) {
		$.each(disable_ids, function(ind, fid) {
			$('#'+fid).prop('disabled', disable);
		});
	}

	setFieldsDisabled(true);
	var backup_button_title = $('#eid-post-comment-button').val();

	$('#eid-post-comment-button').val(tr('POSTING_COMMENT'));
	$('body').css('cursor', 'progress');

	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(json) {
		if (json.error) {
			alert(json.error);
			setFieldsDisabled(false);
			$('#eid-post-comment-button').val(backup_button_title);
			$('body').css('cursor', 'default');
			return;
		}
		if (!json.approved) {
			// clear fields
			$('#fid-comment-body').val('');
			pyrengine_notify($('#eid-comment-notify'), 
				tr('COMMENT_IS_WAITING_FOR_APPROVAL'), $.noop, 10000);
			// display alert
		} else {
			window.location.replace(json.url);
		}
		$('body').css('cursor', 'default');
	}).fail(function(){
		alert(tr('AJAX_REQUEST_ERROR'));
		setFieldsDisabled(false);
		$('#eid-post-comment-button').val(backup_button_title);
		$('body').css('cursor', 'default');
	});
};


window.pyrengine.replyToComment = function(comment_id) {
	var comment_block = $('#c-'+comment_id),
		comment_form = $('#eid-comment-form'),
		link = $('#eid-leave-comment-link-bottom'),
		parent_comment_field = $('#fid-parent-comment');
	
	if (!comment_block.get(0)) {
		return;
	}
	comment_block.append(comment_form);
	
	if (comment_id === -1) {
		link.hide(0);
		parent_comment_field.val('');
	} else {
		parent_comment_field.val(comment_id);
		link.show(0);
	}
	$('#fid-comment-body').focus();
};


window.pyrengine.approveComment = function(url, comment_id) {
	$.ajax({
		url: url,
		type: 'POST'
	}).done(function() {
		// mark corresponding comment as approved
		var c_el = $('#c-'+comment_id),
			ca_el = $('#ca-'+comment_id);
		if (c_el) {
			c_el.removeClass('not-approved');
		}
		if (ca_el) {
			ca_el.hide(0);
		}

	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};


window.pyrengine.showCommentEditForm = function(url, url_fetch, comment_id) {
	// replace comment element with editing form
	var inner = $('#c-inner-'+comment_id),
		comment_el = $('#c-'+comment_id),
		edit_form = $('#c-edit');
	
	// start loading comment data
	$.ajax({
		url: url_fetch,
		dataType: 'json',
		type: 'POST'
	}).done(function(json){
		// fill form fields and show form
		$('#c-edit-comment_id').val(comment_id);
		$('#c-edit-body').val(json.body);
		$('#c-edit-name').val(json.display_name);
		$('#c-edit-email').val(json.email);
		$('#c-edit-website').val(json.website);
		$('#c-edit-date').val(json.date);
		$('#c-edit-ip').val(json.ip_address);
		$('#c-edit-xffip').val(json.xff_ip_address);
		$('#c-edit-is_subscribed').prop('checked', json.is_subscribed === true);
		inner.hide(0);
		comment_el.append(edit_form);
		edit_form.show();
	}).fail(function(){
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};

var deleteComment = function(url, comment_id) {
	$.ajax({
		url: url,
		type: 'POST'
	}).done(function() {
		// delete corresponding comment block
		var c_el = $('#c-'+comment_id);
		c_el.css('background-color', '#f33');
		c_el.hide(0);
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};
window.pyrengine.deleteComment = function(url, comment_id) {
	create_confirm_link('cd-'+comment_id, function() { deleteComment(url, comment_id); });
}

var startBackupRestore = function(url) {
	// display mask layer or something like
	$('#eid-progress').show();

	$.ajax({
		url: url,
		type: 'POST',
		dataType: 'json'
	}).done(function(json) {
		$('#eid-progress').hide();
		if (json.error) {
			$('#eid-error').text(json.error);
			// $('#eid-error').show().delay(5000).hide();
			return;
		}
		alert(tr('BACKUP_RESTORE_COMPLETE'));
		location.assign('/');
	}).fail(function(){
		$('#eid-progress').hide();
		alert(tr('AJAX_REQUEST_ERROR'));
	});
}
window.pyrengine.startBackupRestore = function(url, restore_link_id) {
	// ask confirmation
	create_confirm_link(restore_link_id, function() {startBackupRestore(url);});
};


window.pyrengine.backupNow = function(url) {
	$('#eid-backup-progress').show();
	$.ajax({
		url: url,
		type: 'POST'
	}).done(function() {
		$('#eid-backup-progress').hide();
		location.reload(true);
	}).fail(function() {
		$('#eid-backup-progress').hide();
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};

var pyrengine_file_list_delete_selected = function(table_id, url) {
	// find all checkboxes in the table
	var selected_uids = pyrengine_get_selected_rows(table_id);
	if (selected_uids.length == 0) {
		return;
	}

	$.ajax({
		url: url,
		type: 'POST',
		dataType: 'json',
		data: {
			uids: selected_uids.join(',')
		}
	}).done(function(data){
		$.each(data.deleted, function(ind, id) {
			var el = $('tr[data-row-value="'+id+'"]');
			el.remove();
		});
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});	
};

var pyrengine_backup_list_delete_selected = pyrengine_file_list_delete_selected;
window.pyrengine.deleteSelectedBackups = function (table_id, url) {
	var selected_uids = pyrengine_get_selected_rows(table_id);
	if (selected_uids.length == 0) {
		pyrengine_create_link_notify_box('delete-selected-btn', tr('SELECT_ITEMS_FIRST'));
		return;
	}
	// ask confirmation
	create_confirm_link('delete-selected-btn', function() { pyrengine_backup_list_delete_selected(table_id, url);});
};

})();