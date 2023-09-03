(function() {

var tr = function(s) {
	if (translations[s]) {
		return translations[s];
	}
	return s;
};


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

	pyrengine.field_error('body', null);
	pyrengine.field_error('title', null);
	pyrengine.field_error('shortcut', null);
	pyrengine.field_error('published', null);

	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(data) {
		if (data.success) {
			pyrengine.notify($('#eid-article-notify'), tr('ARTICLE_SAVED'));
		} else {
			pyrengine.notify($('#eid-article-warning'), tr('ARTICLE_SAVE_FAILED'));
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
			pyrengine.field_error(field, error_messages[field].join('<br>'))
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
	pyrengine.create_confirm_link('cd-'+comment_id, function() { deleteComment(url, comment_id); });
}


var startBackupRestore = function(url) {
	// display mask layer or something like
	$('#eid-progress').show();
	$('#eid-error').hide();

	$.ajax({
		url: url,
		type: 'POST',
		dataType: 'json'
	}).done(function(json) {
		$('#eid-progress').hide();
		if (!json.success) {
			$('#eid-error').text(json.error);
			$('#eid-error').show();
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
	pyrengine.create_confirm_link(restore_link_id, function() {startBackupRestore(url);});
};


window.pyrengine.backupNow = function(url) {
	$('#eid-error').hide();
	$('#eid-backup-progress').show();
	$.ajax({
		url: url,
		type: 'POST'
	}).done(function(json) {
		$('#eid-backup-progress').hide();
		if (!json.success) {
			$('#eid-error').text(tr('BACKUP_FAILED_WITH_ERROR').replace('{0}', json.error));
			$('#eid-error').show();
		} else {
			var html = $('#complete-backup-filename').text();
			html = html.replace('{0}', json.backup_file_name);
			$('#complete-backup-filename').text(html);
			$('#eid-backup-done').show();
		}
	}).fail(function() {
		$('#eid-backup-progress').hide();
		alert(tr('AJAX_REQUEST_ERROR'));
	});
};

var pyrengine_file_list_delete_selected = function(table_id, url) {
	$('#eid-error').hide();
	// find all checkboxes in the table
	var selected_uids = pyrengine.get_selected_rows(table_id);
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
	}).done(function(json){
		if (!json.success) {
			$('#eid-error').text(json.error);
			$('#eid-error').show();
		}
		$.each(json.deleted, function(ind, id) {
			var el = $('tr[data-row-value="'+id+'"]');
			el.remove();
		});
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});	
};

var pyrengine_backup_list_delete_selected = pyrengine_file_list_delete_selected;
window.pyrengine.deleteSelectedBackups = function (table_id, url) {
	var selected_uids = pyrengine.get_selected_rows(table_id);
	if (selected_uids.length == 0) {
		pyrengine.create_link_notify_box('delete-selected-btn', tr('SELECT_ITEMS_FIRST'));
		return;
	}
	// ask confirmation
	pyrengine.create_confirm_link('delete-selected-btn', function() { pyrengine_backup_list_delete_selected(table_id, url);});
};


var pyrengine_allow_form_upload;

window.pyrengine.checkFileUploadForm = function(url, form_id) {
	if (pyrengine_allow_form_upload) {
		pyrengine_allow_form_upload = false;
		return true;
	}
	var form = $('#'+form_id);

	var fnf = $('#fid-filename'),
		fdf = $('#fid-filedata');
	
	// forbid empty form submission
	if (fdf.val() == '') {
		var msg = tr('SELECT_FILE_TO_UPLOAD'),
			e = $('#error-filename');
		pyrengine.notify(e, msg);
		fdf.focus();
		return false;
	}

	pyrengine_allow_form_upload = true;
	form.submit();
};


window.pyrengine.uploadFileSelected = function() {
	var ctf = $('#fid-content_type'), 
		fnf = $('#fid-filename'), 
		dltf = $('#fid-dltype'), 
		e = $('#fid-filedata');

	var filename = '';
	var res = /[\/\\]([^\/\\]+)$/.exec(e.val());
	if (res) {
		filename = res[1];
	} else {
		filename = e.val();
	}
	fnf.val(filename);
	// detect values for other fields

	var types = [ [ /\.JPEG$/i, 'image/jpeg' ], [ /\.JPG$/i, 'image/jpeg' ],
			[ /\.PNG$/i, 'image/png' ], [ /\.GIF$/i, 'image/gif' ] ];

	var content_type = '';
	$.each(types, function(ind, t) {
		if (t[0].exec(filename)) {
			content_type = t[1];
			return false;
		}
	});

	switch (content_type) {
	case 'image/jpeg':
	case 'image/png':
	case 'image/gif':
		dltf.val('auto');
		break;

	default:
		dltf.val('download');
	}

	if (content_type === '') {
		content_type = 'application/octet-stream';
	}
	
	fnf.focus();
};

var deleteSelectedFiles = function(table_id, url) {
	// find all checkboxes in the table
	var selected_uids = pyrengine.get_selected_rows(table_id);
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
		if (!data.success) {
			alert(data.error);
		} else {
			$.each(data.deleted, function(ind, id) {
				var el = $('tr[data-row-value="'+id+'"]');
				el.remove();
			});
		}
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});	
};
window.pyrengine.deleteSelectedFiles = function(table_id, url) {
	var selected_uids = pyrengine.get_selected_rows(table_id);
	if (selected_uids.length == 0) {
		pyrengine.create_link_notify_box('delete-selected-btn', tr('SELECT_ITEMS_FIRST'));
		return;
	}
	// ask confirmation
	pyrengine.create_confirm_link('delete-selected-btn', function() { deleteSelectedFiles(table_id, url); });
};

var deleteArticle = function(url, article_id) {
	$.ajax({
		url: url,
		type: 'POST',
		dataType: 'json'
	}).done(function(data) {
		window.location.reload(true);
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
		save_button.removeAttr('disabled');
	});
};
window.pyrengine.deleteArticle = function(url, article_id) {
	pyrengine.create_confirm_link('a-d-'+article_id, function() { deleteArticle(url, article_id);});
}

window.pyrengine.saveSettingsAjax = function(url) {
	var field_names = ['site_title', 'site_base_url', 'site_copyright', 'elements_on_page',
		'admin_notifications_email', 'notifications_from_email', 'image_preview_width', 'google_analytics_id',
		'timezone', 'ui_lang', 'site_search_widget_code', 'ui_theme'];

	var bool_field_names = ['admin_notify_new_comments', 'admin_notify_new_user'];
	var params = {};
	
	$.each(field_names, function(ind, field_name) {
		var e = $('#fid-'+field_name);
		params[field_name] = e.val();
	});
	$.each(bool_field_names, function(ind, field_name) {
		var e = $('#fid-'+field_name);
		if (e.prop('checked')) {
			params[field_name] = true;
		}
	});
	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json',
	}).done(function(json) {
		if (json.errors) {
			var focus_el = false;
			$.each(field_names, function(ind, field_name) {
				var error_value = json.errors[field_name],
					error_el = $('#error-'+field_name);
				
				if (error_value) {
					if (!focus_el) {
						focus_el = $('#fid-'+field_name);
					};
					pyrengine.notify(error_el, error_value, false, -1);
				} else {
					Pyrone_unnotify(error_el);
				}
			});
			if (focus_el) {
				focus_el.focus();
			}
		} else {
			pyrengine.notify($('#eid-notify'), tr('SETTINGS_SAVED'), false, 20000);
		}
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});	
};

window.pyrengine.settingsWidgetsPagesSave = function(url) {
	var e = $('#fid-widget_pages_pages_spec'),
		widget_pages_pages_spec = e.val();
	
	var params = {
		widget_pages_pages_spec: widget_pages_pages_spec
	};
	
	$.ajax({
		url: url,
		type: 'POST',
		data: params,
		dataType: 'json'
	}).done(function(json) {
		if (json.errors) {
		} else {
				pyrengine.notify($('#eid-notify'), tr('SETTINGS_SAVED'), false, 20000);
		} 
	}).fail(function() {
		alert(tr('AJAX_REQUEST_ERROR'));
	});     
};


})();