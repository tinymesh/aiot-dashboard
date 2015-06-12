$(function() {
    var $box = $('#model');
    var $legend = null;
    var mode = 0; // 0 = Occupied, 1 = Time usage, 2 = Quality

    function setMode(new_mode) {
        mode = new_mode;

        $legend.animate({
            'margin-left': '-300px'
        }, 500, function() {
            $legend.html('<div class="icon"></div><ul></ul>');
            if(mode === 0) {
                $legend.find('.icon').html("<i class='fa fa-users'></i>");
                $legend.find('ul')
                    .append('<li><div class="color_block" style="background-color: #f00;"></div> opptatt</li>')
                    .append('<li><div class="color_block" style="background-color: #0f0;"></div> tom</li>');
            } else if(mode == 1) {
            } else {
            }

            $legend.animate({
                'margin-left': '10px'
            }, 500);
        });
    }

    function initModelBox() {
        var token = $box.attr('data-token');
        
        $box.html('<div class="spinner"><i class="fa fa-spin fa-spinner"></i></div><div class="legend"></div><div id="viewer-container" style="width: 100%; height: 100%; margin: auto;"></div>');
        $legend = $box.find('.legend:first');
        $legend.css('margin-left', '-300px');

        // Load the Viewer API
        bimsync.load();
        bimsync.setOnLoadCallback(createViewer);

        // Callback that loads a viewer access token URL
        function createViewer() {
            var $viewer = $('#viewer-container');
            $viewer.viewer('loadurl', 'https://api.bimsync.com/1.0/viewer/access?token=' + token);

            // Make model translucent, otherwise we can't actually see much
            $viewer.bind('viewer.load', function() {
                $('#model .spinner').remove();

                $viewer.viewer('translucentall');

                $viewer.viewer('viewpoint', {
                    direction: {
                        x: -0.577,
                        y: 0.577,
                        z: -0.577
                    },
                    location: {
                        x: 82.85,
                        y: -106.40,
                        z: 110.775
                    },
                    up: {
                        x: 0,
                        y: 0,
                        z: 1
                    },
                    fov: 50,
                    type: 'perspective'
                });

                setMode(0);
                $box.data('updateFunc', function(rec) {
                    if(rec.type !== 'room') {
                        return;
                    }

                    var room_key = rec.key;

                    if(mode === 0) {
                        // Set color based on occupied (red = movement, green = not movement)
                        col = rec.occupied ? '#FF0000' : '#00FF00';

                        $('#viewer-container').viewer('color', col, room_key);
                        $('#viewer-container').viewer('show', room_key);
                    } else if(mode == 1) {
                        col = rec.co2 < 1000 ? '#0f0' : '#ff0';
                        if(rec.co2 > 1500) {
                            col = '#f00';
                        }

                        $('#viewer-container').viewer('color', col, room_key);
                        $('#viewer-container').viewer('show', room_key);
                    } else {
                        col = rec.temperature < 20 ? '#00f' : '#0f0';
                        if(rec.temperature > 23) {
                            col = '#f00';
                        }

                        $('#viewer-container').viewer('color', col, room_key);
                        $('#viewer-container').viewer('show', room_key);
                    }
                });
            });
        }
    }

    initModelBox();
});
