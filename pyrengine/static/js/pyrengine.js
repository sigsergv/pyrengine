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
window.pyrengine.notify = function(elem, text, afterfunc, timeout) {
	if (!timeout) {
		timeout = 3000;
	}
	elem.html(text);
	elem.slideDown(300).delay(timeout).slideUp(300);
};

window.pyrengine.field_error = function(field, msg) {
	if (msg === null) {
		$('#error-'+field).html('').hide(0);
	} else {
		$('#error-'+field).html(msg).show(0);
	}
};

window.pyrengine.get_selected_rows = function(table_id) {
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

window.pyrengine.create_link_notify_box = function(target_id, message) {
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
 * @param {String} position confirmation block display position (relative to target): 'right' (default), 'bottom'
 */
 window.pyrengine.create_confirm_link = function(target_id, callback, position) {
 	var mouse_inside = false;
	var confirm_id = 'confirmlink-' + target_id;
	if ($('#'+confirm_id).get(0)) {
		return;
	}

	var target = document.getElementById(target_id);
	if (!target) {
		return;
	}
	target = $(target);

	var confirmation_el = $('<div class="confirmation-block"><a class="confirm-icon"><span class="fa fa-check-circle"> OK</a></div>').attr({
		href: '#',
		id: confirm_id
	  }).click(function(e) {
	  	  callback.call();
	  	  confirmation_el.remove();
	  	  return false;
	  });

	switch (position) {
	case 'bottom':
		confirmation_el.css({ 'top': target.offset().top + target.outerHeight() + 3, 'left': target.offset().left });
		break;
	default:
		// 'right' is default position
		confirmation_el.css({ 'top': target.offset().top, 'left': target.offset().left + target.outerWidth() + 3 });
	} 
	confirmation_el.on('mouseenter', function() { mouse_inside = true; });
	confirmation_el.on('mouseleave', function() { mouse_inside = false; confirmation_el.remove(); });

	$(document.body).append(confirmation_el);

	setTimeout(function(){
		if (!mouse_inside) {
			confirmation_el.remove();
		}
	}, 1000);
}


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


window.pyrengine.postArticleComment = function() {
	var body = $('#fid-comment-body').val();
	var e = $('#eid-comment-error');
	
	if (body == '') {
		var body_el = $('#fid-comment-body');
		body_el.focus();
		pyrengine.notify(e, tr('COMMENT_BODY_IS_REQUIRED'));
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
	if (is_subscribed === true) {
		params[article_id.substring(19, 27)] = 'true';
	}
	
	var display_name_field = $('#fid-comment-displayname');
	
	if (display_name_field.prop('type') == 'text' && display_name == '') {
		display_name_field.focus();
		pyrengine.notify(e, tr('COMMENT_DISPLAY_NAME_IS_REQUIRED'));
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
			pyrengine.notify($('#eid-comment-notify'), 
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


})();