import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import track
import constants as c
import utils
import iosm


COLOR_LIST = ['orange', 'dodgerblue', 'limegreen', 'hotpink', 'salmon',
              'blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'brown',
              'gold', 'turquoise', 'teal']


def create_map_img(extreme_tiles: tuple, zoom: int) -> np.array:
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    map_img = None

    for x in range(xtile, final_xtile + 1, 1):

        y_img = mpimg.imread(f'tiles/{zoom}/{x}/{ytile}.png')

        for y in range(ytile + 1, final_ytile + 1, 1):
            local_img_path = f'tiles/{zoom}/{x}/{y}.png'
            local_img = mpimg.imread(local_img_path)
            y_img = np.vstack((y_img, local_img))

        if map_img is not None:
            map_img = np.hstack((map_img, y_img))
        else:
            map_img = y_img

    return map_img


def get_extreme_tiles(ob_track: track.Track, zoom: int):
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    xtile, ytile = iosm.deg2num(lat_max, lon_min, zoom)
    final_xtile, final_ytile = iosm.deg2num(lat_min, lon_max, zoom)

    return xtile, ytile, final_xtile, final_ytile


def get_map_box(extreme_tiles, zoom):
    xtile, ytile, final_xtile, final_ytile = extreme_tiles
    ymax, xmax = iosm.num2deg(final_xtile + 1, ytile, zoom)
    ymin, xmin = iosm.num2deg(xtile, final_ytile + 1, zoom)
    bbox = (xmin, xmax, ymin, ymax)
    return bbox


def generate_map(ob_track: track.Track) -> np.array:
    # Define map perspective
    lat_min, lat_max, lon_min, lon_max = ob_track.extremes
    zoom = utils.auto_zoom(lat_min, lon_min, lat_max, lon_max)

    extreme_tiles = get_extreme_tiles(ob_track, zoom)
    extreme_tiles_expanded = (extreme_tiles[0] - c.margin_outbounds,  # x
                              extreme_tiles[1] - c.margin_outbounds,  # y
                              extreme_tiles[2] + c.margin_outbounds,  # xfinal
                              extreme_tiles[3] + c.margin_outbounds)  # yfinal

    # Download missing tiles
    iosm.download_tiles(lat_min, lon_min, lat_max, lon_max,
                        max_zoom=zoom, extra_tiles=c.margin_outbounds)

    # Generate map image
    map_img = create_map_img(extreme_tiles_expanded, zoom)

    # Define map box
    bbox = get_map_box(extreme_tiles_expanded, zoom)

    return map_img, bbox


def get_distance_label(ob_track: track.Track, segment_id: int = 1,
                       total: bool = False) -> str:
    if total:
        distance = ob_track.total_distance
    else:
        segment = ob_track.get_segment(segment_id)
        first = segment.iloc[0]
        last = segment.iloc[-1]

        if np.isnan(first['distance']):
            distance = last['distance']
        else:
            distance = last['distance'] - first['distance']

    if distance < 5:
        label = f'{distance:.2f} km'
    else:
        label = f'{distance:.1f} km'

    return label


def get_elevation_label(ob_track: track.Track, magnitude: str,
                        segment_id: int = 1, total: bool = False) -> str:
    if total:
        if 'pos' in magnitude:
            elevation = ob_track.total_uphill
        elif 'neg' in magnitude:
            elevation = ob_track.total_downhill
        else:
            elevation = 0
            print("[WARNING] Wrong input in function get_elevation_label")
    else:
        segment = ob_track.get_segment(segment_id)
        first = segment.iloc[0]
        last = segment.iloc[-1]

        if np.isnan(first[magnitude]):
            elevation = last[magnitude]
        else:
            elevation = last[magnitude] - first[magnitude]

    if abs(elevation) < 10:
        label = f'{elevation:.1f} m'
    else:
        label = f'{int(elevation)} m'

    if elevation > 0:
        label = f'+{label}'

    return label


def plot_track_info(ob_track: track.Track, ax: plt.Figure.gca):
    ax.cla()

    # Initialize table
    cell_text = []
    track_color = []

    # Build segments info table
    segments_id = ob_track.track.segment.unique()

    for cc, seg_id in zip(COLOR_LIST, segments_id):
        distance_lbl = get_distance_label(ob_track, segment_id=seg_id)
        gained_elevation_lbl = get_elevation_label(ob_track, 'ele_pos_cum',
                                                   segment_id=seg_id)
        lost_elevation_lbl = get_elevation_label(ob_track, 'ele_neg_cum',
                                                 segment_id=seg_id)

        cell_text.append(['',  # cell for color
                          distance_lbl,
                          gained_elevation_lbl,
                          lost_elevation_lbl])  # is negative

        track_color.append(cc)

    # Get info for the full track
    distance_lbl = get_distance_label(ob_track, -1, total=True)
    gained_elevation_lbl = get_elevation_label(ob_track, 'ele_pos_cum',
                                               total=True)
    lost_elevation_lbl = get_elevation_label(ob_track, 'ele_neg_cum',
                                             total=True)

    cell_text.append(['TOTAL',
                      distance_lbl,
                      gained_elevation_lbl,
                      lost_elevation_lbl])

    # Create table
    my_table = ax.table(cellText=cell_text,
                        loc='upper right',
                        edges='open',
                        colWidths=[1/6, 1/4, 1/4, 1/4])

    # Beauty salon
    my_table.set_fontsize(14)
    for row_idx, (row, row_cc) in enumerate(zip(cell_text, track_color)):
        my_table[row_idx, 0].visible_edges = 'BLRT'
        my_table[row_idx, 0].set_facecolor(row_cc)
        my_table[row_idx, 0].set_edgecolor('white')


def plot_no_info(ax: plt.Figure.gca):
    ax.cla()
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(False)


def get_closest_segment(df_track: pd.DataFrame, point: tuple[float, float]):
    df_track['point_distance'] = (df_track.lon - point[0])**2 + \
                           (df_track.lat - point[1])**2
    min_row = \
        df_track[df_track.point_distance == df_track.point_distance.min()]
    min_distance = min_row.point_distance.iloc[0]
    min_segment = min_row.segment.iloc[0]
    df_track.drop('point_distance', axis=1, inplace=True)

    return min_distance, min_segment


def plot_track(ob_track: track.Track, ax: plt.Figure.gca, fig: plt.Figure):
    ax.cla()

    # Plot map
    map_img, bbox = generate_map(ob_track)
    ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

    # Plot track
    segments_id = ob_track.track.segment.unique()
    for cc, seg_id in zip(COLOR_LIST, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.plot(segment.lon, segment.lat, color=cc,
                linewidth=1, marker='o', markersize=2, zorder=10)

    # Beauty salon
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)

    # Interactivity
    def on_click(event):

        # Find closest line
        point_distance, selected_segment = \
            get_closest_segment(ob_track.track, (event.xdata, event.ydata))
        print()
        print(point_distance, selected_segment)
        select_segment = [False] * (max(segments_id) + 1)
        if point_distance < 5e-7:
            try:
                select_segment[selected_segment] = True
            except IndexError as e:
                print(f'IndexError: {e}')
                print(select_segment)
                print(selected_segment)
                print(segments_id)
                print()

        # Plot map
        map_img, bbox = generate_map(ob_track)
        ax.imshow(map_img, zorder=0, extent=bbox, aspect='equal')

        print(select_segment)
        # Plot track
        for cc, seg_id in zip(COLOR_LIST, segments_id):
            segment = ob_track.get_segment(seg_id)

            if select_segment[seg_id]:
                print(f'{seg_id}: selected')
                ax.plot(segment.lon, segment.lat, color=cc,
                        linewidth=2, marker='o', markersize=2, zorder=10)
            else:
                print(f'{seg_id}: not selected')
                ax.plot(segment.lon, segment.lat, color=cc,
                        linewidth=1, markersize=1, zorder=10)

        fig.canvas.draw()

    fig.canvas.mpl_connect('button_press_event', on_click)


def plot_elevation(ob_track: track.Track, ax: plt.Figure.gca):
    ax.cla()

    # Plot elevation
    segments_id = ob_track.track.segment.unique()

    for cc, seg_id in zip(COLOR_LIST, segments_id):
        segment = ob_track.get_segment(seg_id)
        ax.fill_between(segment.distance, segment.ele, alpha=0.2, color=cc)
        ax.plot(segment.distance, segment.ele, linewidth=2, color=cc)

    ax.set_ylim((ob_track.track.ele.min() * 0.8,
                 ob_track.track.ele.max() * 1.2))

    # Set labels
    dist_label = [f'{int(item)} km' for item in ax.get_xticks()]
    ele_label = [f'{int(item)} m' for item in ax.get_yticks()]

    if len(dist_label) != len(set(dist_label)):
        dist_label = [f'{item:.1f} km' for item in ax.get_xticks()]

    ax.set_xticklabels(dist_label)
    ax.set_yticklabels(ele_label)

    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=True)
    ax.tick_params(axis='y', left=False, right=False, labelleft=True)

    ax.grid(color='white')  # for some reason grid is removed from ggplot


def plot_world(ax: plt.Figure.gca):
    ax.clear()
    world_img = mpimg.imread(f'tiles/0/0/0.png')
    ax.imshow(world_img, zorder=0, aspect='equal')  # aspect is equal to ensure
    # square pixel
    ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)


def plot_no_elevation(ax: plt.Figure.gca):
    with plt.style.context('ggplot'):
        ax.plot()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.tick_params(axis='x', bottom=False, top=False, labelbottom=False)
        ax.tick_params(axis='y', left=False, right=False, labelleft=False)
