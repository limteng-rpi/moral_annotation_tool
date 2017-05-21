/**
 * Created by limteng on 5/20/17.
 */

$(document).ready(function () {
    initialize_grids();

}).on('click', '#add-btn', add_document)
    .on('click', '#remove-btn', remove_document);

function initialize_grids() {
    $('#dataset').w2grid({
        name: 'dataset',
        header: 'Dataset',
        show: {
            header: true,
            toolbar: true,
            footer: true,
            selectColumn: true
        },
        columns: [
            {
                field: 'tid',
                caption: 'Tweet ID',
                size: '40%',
                sortable: true,
                resizable: true
            },
            {
                field: 'dataset',
                caption: 'Dataset',
                size: '15%',
                sortable: true,
                resizable: true
            },
            {
                field: 'retweet',
                caption: 'Retweet',
                size: '15%',
                sortable: true,
                resizable: true
            },
            {
                field: 'timestamp',
                caption: 'Timestamp',
                size: '30%',
                sortable: true,
                resizable: true
            }
        ],
        searches: [
            {field: 'tid', caption: 'Tweet ID', type: 'text'},
            {field: 'dataset', caption: 'Dataset', type: 'text'}
        ]
    });

    $('#document').w2grid({
        name: 'document',
        header: 'Document',
        show: {
            header: true,
            toolbar: true,
            footer: true,
            selectColumn: true
        },
        columns: [
            {
                field: 'tid',
                caption: 'Tweet ID',
                size: '40%',
                sortable: true,
                resizable: true
            },
            {
                field: 'dataset',
                caption: 'Dataset',
                size: '15%',
                sortable: true,
                resizable: true
            },
            {
                field: 'retweet',
                caption: 'Retweet',
                size: '15%',
                sortable: true,
                resizable: true
            },
            {
                field: 'timestamp',
                caption: 'Timestamp',
                size: '30%',
                sortable: true,
                resizable: true
            }
        ],
        searches: [
            {field: 'tid', caption: 'Tweet ID', type: 'text'},
            {field: 'dataset', caption: 'Dataset', type: 'text'}
        ]
    });

    $.getJSON('/operation?entry=get_dataset_and_document', function(response) {
        if (response.code === 200) {
            var dataset = response.result.dataset;
            var dataset_records = [];
            $.each(dataset, function(i, doc) {
                dataset_records.push({
                    'recid': i,
                    'id': doc.id,
                    'tid': doc.tid,
                    'timestamp': doc.timestamp,
                    'dataset': doc.dataset,
                    'retweet': doc.retweet
                });
            });
            w2ui.dataset.add(dataset_records);

            var offset = dataset_records.length;
            var document = response.result.document;
            var document_records = [];
            $.each(document, function(i, doc) {
                document_records.push({
                    'recid': i + offset,
                    'id': doc.id,
                    'tid': doc.tid,
                    'timestamp': doc.timestamp,
                    'dataset': doc.dataset,
                    'retweet': doc.retweet
                });
            });
            w2ui.document.add(document_records);
        }
    });
}

function add_document() {
    var dataset = w2ui.dataset;
    var document = w2ui.document;
    var selected = dataset.getSelection();
    var records = [];
    var id_list = [];
    $.each(selected, function(i, recid) {
        var record = dataset.get(recid);
        records.push(record);
        id_list.push(record.id);
    });
    if (id_list.length > 0) {
        $.post('/operation', {
            entry: 'add_document',
            id_list: JSON.stringify(id_list)
        }, function (response) {
            if (response.code === 200) {
                document.add(records);
                dataset.selectNone();
                dataset.remove.apply(dataset, selected);
            }
        });
    }
}

function remove_document() {
    var dataset = w2ui.dataset;
    var document = w2ui.document;
    var selected = document.getSelection();
    var records = [];
    var id_list = [];
    $.each(selected, function(i, recid) {
        var record = document.get(recid);
        records.push(record);
        id_list.push(record.id);
    });
    if (id_list.length > 0) {
        $.post('/operation', {
            entry: 'remove_document',
            id_list: JSON.stringify(id_list)
        }, function (response) {
            if (response.code === 200) {
                dataset.add(records);
                document.selectNone();
                document.remove.apply(document, selected);
            }
        });
    }
}