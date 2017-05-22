/**
 * Created by limteng on 5/21/17.
 */
var __status = {};

$(document).ready(function () {
    init_doc_status();
}).on('click', 'span.doc-body-char', char_click)
    .on('click', 'button.category-btn', category_btn_click)
    .on('click', 'button.skip-btn', skip_btn_click)
    .on('click', 'button.unclear-btn', unclear_btn_click)
    .on('click', 'button#submit-btn', submit_btn_click);

function init_doc_status() {
    $('.doc-item').each(function (i, v) {
        v = $(v);
        var uuid = v.attr('uuid');
        __status[uuid] = {
            'step': -1,
            'start': -1,
            'end': -1
        }
    });
}

function char_click() {
    var char = $(this);
    var char_index = parseInt(char.attr('char-index'));
    var uuid = char.attr('uuid');

    var doc_status = __status[uuid];
    if (char.attr('hl') === 'true') {
        $('.doc-body-char[uuid="' + uuid + '"]').attr('hl', 'false');
        __status[uuid].step = -1;
        __status[uuid].start = -1;
        __status[uuid].end = -1;
    } else {
        var step = doc_status.step;
        switch (step) {
            case -1:
                $('.doc-body-char[uuid="' + uuid + '"]').attr('hl', 'false');
                __status[uuid].start = char_index;
                char.attr('hl', 'true');
                __status[uuid].step = 1;
                break;
            case 1:
                if (__status[uuid].start > char_index) {
                    __status[uuid].end = __status[uuid].start;
                    __status[uuid].start = char_index;
                } else {
                    __status[uuid].end = char_index;
                }
                console.log(__status[uuid].start);
                console.log(__status[uuid].end);
                $('.doc-body-char[uuid="' + uuid + '"]').each(function(i, v) {
                    v = $(v);
                    if (parseInt(v.attr('char-index')) >= __status[uuid].start
                        && parseInt(v.attr('char-index')) <= __status[uuid].end) {
                        v.attr('hl', 'true');
                    }
                });
                __status[uuid].step = -1;
                __status[uuid].start = -1;
                __status[uuid].end = -1;
                break;
        }
    }
}

function category_btn_click() {
    var btn = $(this);
    var uuid = btn.attr('uuid');
    var value = btn.attr('value');
    if (value === 'nm') {
        if (btn.attr('labeled') === 'true') {
            btn.attr('labeled', 'false');
        } else {
            $('.category-btn[uuid="' + uuid + '"]').attr('labeled', 'false');
            btn.attr('labeled', 'true');
        }
    } else {
        if (btn.attr('labeled') === 'true') {
            btn.attr('labeled', 'false');
        } else {
            $('.category-btn[uuid="' + uuid + '"][value="nm"]').attr('labeled', 'false');
            btn.attr('labeled', 'true');
        }
    }
}

function unclear_btn_click() {
    var btn = $(this);
    var uuid = btn.attr('uuid');
    $('.skip-btn[uuid="' + uuid + '"]').attr('labeled', 'false');
    if (btn.attr('labeled') === 'true') {
        btn.attr('labeled', 'false');
    } else {
        btn.attr('labeled', 'true');
    }
}

function skip_btn_click() {
var btn = $(this);
    var uuid = btn.attr('uuid');
    $('.unclear-btn[uuid="' + uuid + '"]').attr('labeled', 'false');
    if (btn.attr('labeled') === 'true') {
        btn.attr('labeled', 'false');
    } else {
        btn.attr('labeled', 'true');
    }
}

function extract_annotation(uuid) {
    var annotation = {
        uuid: uuid,
        dataset: $('#main').attr('dataset'),
        timestamp: Date.now()
    };
    annotation['comment'] = $('input.comment-input[uuid="' + uuid + '"]').val();
    if ($('.unclear-btn[uuid="' + uuid + '"]').attr('labeled') === 'true') {
        annotation['unclear'] = true;
        return annotation;
    } else if ($('.skip-btn[uuid="' + uuid + '"]').attr('labeled') === 'true') {
        annotation['skip'] = true;
        return annotation;
    } else {
        // get category
        var category = [];
        $('.category-btn[uuid="' + uuid + '"][labeled="true"]').each(function(i, v) {
            v = $(v);
            category.push(v.attr('value'));
        });
        if (category.length === 0) {
            annotation['unlabeled'] = true;
            return annotation;
        } else {
            annotation['category'] = category;
        }
        // get issue
        var issue_start = -1;
        var issue_end = -1;
        var issue = '';
        $('.doc-body-char[uuid="' + uuid + '"][hl="true"]').each(function (i, c) {
            c = $(c);
            var index = parseInt(c.attr('char-index'));
            if (issue_start === -1 || index < issue_start)
                issue_start = index;
            if (issue_end === -1 || index > issue_end)
                issue_end = index;
        });
        for (var i = issue_start; i <= issue_end; i++) {
            issue += $('.doc-body-char[uuid="' + uuid + '"][char-index="' + i + '"]').text();
        }
        annotation['issue_start'] = issue_start;
        annotation['issue_end'] = issue_end;
        annotation['issue'] = issue;
        // get abstract issue
        annotation['abstract_issue'] = $('input.issue-input[uuid="' + uuid + '"]').val();
        return annotation;
    }
}

function submit_btn_click() {
    var annotation_list = [];
    $.each(__status, function(k, v) {
        var annotation = extract_annotation(k);
        if (!('unlabeled' in annotation && annotation.unlabeled)) {
            annotation_list.push(annotation);
        }
    });
    if (annotation_list.length > 0) {
        $.post('/annotation', {
            'annotation_list': JSON.stringify(annotation_list)
        }, function(response) {
            if (response.code === 200) {
                $('html, body').animate({ scrollTop: 0 }, 'fast', function(){
                    location.reload();
                });
            } else {
            }
        }, 'json');
    }
}