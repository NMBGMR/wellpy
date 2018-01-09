# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os

from enable.component_editor import ComponentEditor
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Button, Float, Property, Int, Enum, Bool, Event
from traitsui.api import View, UItem, TabularEditor, Item, HGroup, VGroup, spring, EnumEditor
from traitsui.tabular_adapter import TabularAdapter

from globals import FILE_DEBUG
from wellpy.sigproc import SMOOTH_METHODS


class PointIDAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('DateInstalled', 'install_date'),
               ('Serial', 'serial_num')]

    name_width = Int(60)
    font = 'arial 10'


class WellCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('object.model.plot_container',
                       style='custom', editor=ComponentEditor()))
        return v


class ToolboxPane(TraitsDockPane):
    id = 'wellpy.toolbox.pane'
    name = 'Toolbox'
    fix_adj_head_data_button = Button('Remove Offsets/Zeros')
    fix_depth_to_water_data_button = Button('Remove Offsets/Zeros')

    constant_offset = Float
    adj_head_threshold = Float(0.25)
    depth_to_water_threshold = Float(0.25)

    smooth_data_button = Button('Smooth')
    window = Int(11)
    method = Enum(SMOOTH_METHODS)

    omit_selection_button = Button('Omit Selected Data')
    snap_to_selected_button = Button('Snap To Selected')

    calculate_button = Button('Calculate')
    correct_drift = Bool
    drift_correction_direction = Enum('Forward', 'Reverse')
    save_db_button = Button('Save DB')
    save_csv_button = Button('Save CSV')
    save_png_button = Button('Save PNG')
    save_pdf_button = Button('Save PDF')

    undo_button = Button('Undo')

    def _snap_to_selected_button_fired(self):
        self.model.snap()

    def _omit_selection_button_fired(self):
        self.model.omit_selection()

    def _save_pdf_button_fired(self):
        self.model.save_pdf()

    def _save_png_button_fired(self):
        self.model.save_png()

    def _save_db_button_fired(self):
        self.model.save_db()

    def _save_csv_button_fired(self):
        dlg = FileDialog(action='save as', default_directory=os.path.expanduser('~'))

        if dlg.open() == OK:
            self.model.save_csv(dlg.path)

    def _constant_offset_changed(self, new):
        self.model.apply_constant_offset(new)

    def _fix_adj_head_data_button_fired(self):
        self.model.fix_adj_head_data(self.adj_head_threshold)

    def _fix_depth_to_water_data_button_fired(self):
        self.model.fix_depth_to_water_data(self.depth_to_water_threshold)

    def _undo_button_fired(self):
        self.model.unfix_adj_head_data()

    # def _smooth_data_button_fired(self):
    #     self.model.smooth_data(self.window, self.method)

    def _calculate_button_fired(self):
        self.model.calculate_depth_to_water(self.correct_drift)

    def traits_view(self):
        manual_grp = VGroup(UItem('pane.omit_selection_button'),
                            UItem('pane.snap_to_selected_button'),
                            # Item('pane.constant_offset', label='Constant Offset'),
                            show_border=True, label='Manual')

        auto_grp = VGroup(HGroup(Item('pane.adj_head_threshold', label='Threshold'),
                                 UItem('pane.fix_adj_head_data_button'),
                                 UItem('pane.undo_button')),
                          show_border=True, label='Adjusted Head')
        # smooth_grp = VGroup(HGroup(UItem('pane.method'), Item('pane.window')),
        #                     UItem('pane.smooth_data_button'),
        #                     show_border=True,
        #                     label='Smooth')

        calculate_grp = VGroup(HGroup(Item('pane.correct_drift'),
                                      Item('pane.drift_correction_direction'),
                                      UItem('pane.calculate_button')),
                               HGroup(UItem('pane.save_db_button'),
                                      UItem('pane.save_csv_button'),
                                      UItem('pane.save_pdf_button'),
                                      # UItem('pane.save_png_button')
                                      ),

                               # HGroup(Item('pane.depth_to_water_threshold', label='Threshold'),
                               # UItem('pane.fix_depth_to_water_data_button')),

                               label='Depth To Water',
                               show_border=True)
        v = View(VGroup(manual_grp,
                        auto_grp,
                        # smooth_grp,
                        calculate_grp))
        return v


class AutoResultsTabularAdapter(TabularAdapter):
    columns = [('Start', 'start'),
               ('End', 'end'),
               ('Offset', 'offset')]

    # start_text = Property
    # def _get_start_text(self):
    #     return self.item.start.isoformat()


class AutoResultsPane(TraitsDockPane):
    id = 'wellpy.autoresults.pane'
    name = 'AutoResults'

    def traits_view(self):
        v = View(UItem('auto_results', editor=TabularEditor(adapter=AutoResultsTabularAdapter())))
        return v


class QCPane(TraitsDockPane):
    id = 'wellpy.qc.pane'
    name = 'QC'

    apply_qc_button = Button('Apply QC')

    load_qc_button = Button('Refresh QC Needed')
    dclicked = Event

    def _dclicked_fired(self):
        self.model.load_qc_data()

    def _apply_qc_button_fired(self):
        self.model.apply_qc()

    def _load_qc_button_fired(self):
        self.model.load_qc()

    def traits_view(self):
        pa = PointIDAdapter()
        pa.columns = pa.columns[:1]

        v = View(HGroup(UItem('pane.apply_qc_button'),
                        UItem('pane.load_qc_button')),
                 UItem('qc_point_ids',
                       editor=TabularEditor(selected='selected_qc_point_id',
                                            dclicked='pane.dclicked',
                                            editable=False,
                                            adapter=pa)))
        return v


class WellPane(TraitsDockPane):
    id = 'wellpy.well.pane'
    name = 'Well'
    open_file_button = Button('Open')
    retrieve_depth_to_water_button = Button('Retrieve')

    def _retrieve_depth_to_water_button_fired(self):
        self.model.retrieve_depth_to_water()

    def _open_file_button_fired(self):

        if FILE_DEBUG:
            self.model.path = FILE_DEBUG
            self.model.load_file(FILE_DEBUG)
        else:
            dlg = FileDialog(action='open', default_directory=os.path.expanduser('~'))

            if dlg.open() == OK:
                if os.path.isfile(dlg.path):
                    self.model.path = dlg.path
                    self.model.load_file(dlg.path)

    def traits_view(self):
        site_grp = VGroup(HGroup(UItem('point_id_entry', tooltip='Fuzzy filter the available Sites'),
                                 UItem('pane.retrieve_depth_to_water_button',
                                       tooltip='Retrieve "Depth To Water" from the database for the selected Site',
                                       enabled_when='selected_point_id')),
                          UItem('filtered_point_ids',
                                editor=TabularEditor(selected='selected_point_id',
                                                     editable=False,
                                                     scroll_to_row='scroll_to_row',
                                                     adapter=PointIDAdapter())),
                          show_border=True,
                          label='Site')
        df_grp = HGroup(UItem('filename', style='readonly'),
                        spring,
                        UItem('pane.open_file_button'),
                        show_border=True,
                        label='Diver File')

        metadata_grp = VGroup(Item('data_source', editor=EnumEditor(name='data_sources')),
                              Item('measurement_agency', editor=EnumEditor(name='measurement_agencies')),
                              Item('measurement_method', editor=EnumEditor(name='measurement_methods')),
                              # Item('note'),
                              show_border=True, label='Metadata')

        v = View(VGroup(df_grp, site_grp, metadata_grp))

        return v

# ============= EOF =============================================
