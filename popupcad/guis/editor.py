# -*- coding: utf-8 -*-
"""
Written by Daniel M. Aukes and CONTRIBUTORS
Email: danaukes<at>seas.harvard.edu.
Please see LICENSE for full license.
"""

import sys
import os

import qt.QtCore as qc
import qt.QtGui as qg
import glob
import imp

import popupcad

from popupcad.filetypes.design import Design
import popupcad.guis.icons
#

class NoOutput(Exception):
    def __init__(self):
        Exception.__init__(self,'Operation has not been processed due to a previous exception')

class Editor(popupcad.widgets.widgetcommon.WidgetBasic, qg.QMainWindow):

    '''
    Editor Class

    The Editor is the main widget for popupCAD.
    '''
    gridchange = qc.Signal()
    operationedited = qc.Signal(object)
    operationadded = qc.Signal(object)

    def __init__(self, parent=None, **kwargs):
        """Initialize Editor

        :param parent: Parent Widget(if any)
        :type parent: QWidget
        :returns:  nothing
        :raises: nothing
        """
        super(Editor, self).__init__(parent)
        self.error_log = popupcad.widgets.errorlog.ErrorLog()
        self.safe_init(parent, **kwargs)

    
    def safe_init(self, parent=None, **kwargs):
        self.scene = popupcad.graphics2d.graphicsscene.GraphicsScene()
        self.view_2d = popupcad.graphics2d.graphicsview.GraphicsView(
            self.scene)
        self.view_2d.scrollhand()
        self.setCentralWidget(self.view_2d)

        self.setTabPosition(qc.Qt.AllDockWidgetAreas, qg.QTabWidget.South)

        self.operationeditor = popupcad.widgets.dragndroptree.DirectedDraggableTreeWidget()
        self.operationeditor.enable()

        self.layerlistwidget = popupcad.widgets.listeditor.ListSelector()

        self.operationdock = qg.QDockWidget()
        self.operationdock.setWidget(self.operationeditor)
        self.operationdock.setAllowedAreas(qc.Qt.AllDockWidgetAreas)
        self.operationdock.setWindowTitle('Operations')
        self.addDockWidget(qc.Qt.LeftDockWidgetArea, self.operationdock)

        self.layerlistwidgetdock = qg.QDockWidget()
        self.layerlistwidgetdock.setWidget(self.layerlistwidget)
        self.layerlistwidgetdock.setAllowedAreas(qc.Qt.AllDockWidgetAreas)
        self.layerlistwidgetdock.setWindowTitle('Layers')
        self.addDockWidget(qc.Qt.LeftDockWidgetArea, self.layerlistwidgetdock)

        self.view_3d = popupcad.graphics3d.gl_viewer.GLObjectViewer(self)
        self.view_3d_dock = qg.QDockWidget()
        self.view_3d_dock.setWidget(self.view_3d)
        self.view_3d_dock.setAllowedAreas(qc.Qt.AllDockWidgetAreas)
        self.view_3d_dock.setWindowTitle('3D Visualization')
        self.addDockWidget(qc.Qt.RightDockWidgetArea, self.view_3d_dock)

        self.operationeditor.currentRowChanged.connect(
            self.showcurrentoutput_inner)
        self.layerlistwidget.itemSelectionChanged.connect(
            self.showcurrentoutput)
        self.setWindowTitle('Editor')
        self.operationeditor.signal_edit.connect(self.editoperation)
        self.newfile()
        self.operationadded.connect(self.newoperationslot)
        self.operationedited.connect(self.editedoperationslot)

        self.createActions()
        self.backuptimer = qc.QTimer()
        self.backuptimer.setInterval(popupcad.backup_timeout)
        self.backuptimer.timeout.connect(self.autosave)
        self.backuptimer.start()

        self.operationdock.closeEvent = lambda event: self.action_uncheck(
            self.act_view_ops)
        self.layerlistwidgetdock.closeEvent = lambda event: self.action_uncheck(
            self.act_view_layers)
        self.view_3d_dock.closeEvent = lambda event: self.action_uncheck(
            self.act_view_3d)
        self.error_log.closeEvent = lambda event: self.action_uncheck(
            self.act_view_errors)

#        self.set_nominal_size()
#        self.move_center()

    def autosave(self):
        self.design.backup(popupcad.backupdir,'_autosave_')
        
    def show_hide_view_3d(self):
        if self.m.actions['view_3d'].isChecked():
            self.view_3d_dock.show()
        else:
            self.view_3d_dock.hide()

    def show_hide_operationdock(self):
        if self.m.actions['view_operations'].isChecked():
            self.operationdock.show()
        else:
            self.operationdock.hide()

    def show_hide_layerlistwidgetdock(self):
        if self.m.actions['view_layers'].isChecked():
            self.layerlistwidgetdock.show()
        else:
            self.layerlistwidgetdock.hide()

    def show_hide_error_log(self):
        if self.m.actions['view_error_log'].isChecked():
            self.error_log.show()
        else:
            self.error_log.hide()
        
    def createActions(self):
        import popupcad.guis.actions
        self.m = popupcad.guis.actions.m
        self.m.build(self)
#        self.m.set_parent(self)
        top_key = self.m.top_menu_key
        menu_struct =self.m.menu_struct
        top_keys = menu_struct[top_key]
        top_items = [self.m.all_items[key] for key in top_keys]
        
        menu_bar = qg.QMenuBar()
        [menu_bar.addMenu(item) for item in top_items]
        self.setMenuBar(menu_bar)    
        
    def new_cleanup2(self):
        self.newoperation(popupcad.manufacturing.cleanup2.Cleanup2)
    def new_cleanup3(self):
        self.newoperation(popupcad.manufacturing.cleanup3.Cleanup3)
    def new_simplify2(self):
        self.newoperation(popupcad.manufacturing.simplify2.Simplify2)
    def new_jointop3(self):
        self.newoperation(popupcad.manufacturing.joint_operation3.JointOperation3)
    def new_holeop(self):
        self.newoperation(popupcad.manufacturing.hole_operation.HoleOperation)
    def new_freezeop(self):
        self.newoperation(popupcad.manufacturing.freeze.Freeze)
    def new_cross_section(self):
        self.newoperation(popupcad.manufacturing.cross_section.CrossSection)
    def new_subpo(self):
        self.newoperation(popupcad.manufacturing.sub_operation2.SubOperation2)
    def new_codeop(self):
        self.newoperation(popupcad.manufacturing.code_exec_op.CodeExecOperation)
#    def new_(self):
#        self.newoperation()
#    def new_(self):
#        self.newoperation()
#    def new_(self):
#        self.newoperation()
#    def new_(self):
#        self.newoperation()
#    def new_(self):
#        self.newoperation()
#        self.tools1.append({'text': 'Code Exec','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.code_exec_op.CodeExecOperation)}})
        
#    def createActions(self):
##        icons = popupcad.guis.icons.build()
#
#        self.fileactions = []
#        self.fileactions.append({'text': "&New",'kwargs': {'icon': icons['new'],'shortcut': qg.QKeySequence.New,'statusTip': "Create a new file",'triggered': self.newfile}})
#        self.fileactions.append({'text': "&Open...",'kwargs': {'icon': icons['open'],'shortcut': qg.QKeySequence.Open,'statusTip': "Open an existing file",'triggered': self.open}})
#        self.fileactions.append({'text': "&Save",'kwargs': {'icon': icons['save'],'shortcut': qg.QKeySequence.Save,'statusTip': "Save the document to disk",'triggered': self.save}})
#        self.fileactions.append({'text': "Save &As...",'kwargs': {'icon': icons['save'],'shortcut': qg.QKeySequence.SaveAs,'statusTip': "Save the document under a new name",'triggered': self.saveAs}})
#        self.fileactions.append({'text': "Upgrade",'kwargs': {'statusTip': "Upgrade the file",'triggered': self.upgrade}})
#        self.fileactions.append({'text': 'Export to stl', 'kwargs': {'icon': icons['export'],'statusTip': "Exports to a stl file",'triggered': self.export_stl}})
#        self.fileactions.append({'text': '&Export to SVG', 'kwargs': {'icon': icons['export'], 'triggered': self.exportLayerSVG}})
#        self.fileactions.append({'text': 'Export to dxf', 'kwargs': {'icon': icons['export'],'statusTip': "Exports to a dxf file",'triggered': self.export_dxf}})
#        self.fileactions.append({'text': 'Export layers to dxf', 'kwargs': {'icon': icons['export'],'statusTip': "Exports to a dxf file",'triggered': self.export_dxf_layers}})
#        self.fileactions.append({'text': 'Export to dae', 'kwargs': {'icon': icons['export'],'statusTip': "Exports to a dae file",'triggered': self.export_dae}})
#
#        self.fileactions.append({'text': "Save Joint Defs", 'kwargs': {'triggered': self.save_joint_def}})
#        self.fileactions.append({'text': "Export Laminate", 'kwargs': {'triggered': self.export_laminate}})
#        self.fileactions.append({'text': "Regen ID", 'kwargs': {'triggered': self.regen_id, }})
##        self.fileactions.append({'text': "Preferences...", 'kwargs': {'triggered': self.preferences}})
#        self.fileactions.append({'text': "Render Icons", 'kwargs': {'triggered': self.gen_icons}})
#        self.fileactions.append({'text': "Build Documentation", 'kwargs': {'triggered': self.build_documentation}})
#        self.fileactions.append({'text': "License", 'kwargs': {'triggered': self.show_license}})
#        self.fileactions.append({'text': "Update...",'kwargs': {'triggered': self.download_installer}})
#
#        self.projectactions = []
#        self.projectactions.append({'text': '&Rebuild','kwargs': {'icon': icons['refresh'],'shortcut': 'Ctrl+Shift+R','triggered': self.reprocessoperations_outer}})
#
#        def dummy(action):
#            action.setCheckable(True)
#            action.setChecked(True)
#            self.act_autoreprocesstoggle = action
#        self.projectactions.append({'text': 'Auto Reprocess', 'kwargs': {}, 'prepmethod': dummy})
#        
#        self.projectactions.append(None)
#        self.projectactions.append({'text': 'Layer Order...', 'kwargs': {'triggered': self.editlayers}})
#        self.projectactions.append({'text': 'Laminate Properties...', 'kwargs': {'triggered': self.editlaminate}})
#        self.projectactions.append({'text': 'Sketches...', 'kwargs': {'triggered': self.sketchlist}})
#        self.projectactions.append({'text': 'SubDesigns...', 'kwargs': {'triggered': self.subdesigns}})
#        self.projectactions.append({'text': 'Replace...', 'kwargs': {'triggered': self.replace}})
#        self.projectactions.append({'text': 'Insert Laminate Op and Replace...', 'kwargs': {'triggered': self.insert_and_replace}})
#        self.projectactions.append({'text': 'Hierarchy', 'kwargs': {'triggered': self.operation_network}})
#
#        self.viewactions = []
#
#        def dummy(action):
#            action.setCheckable(True)
#            action.setChecked(False)
#            self.act_view_3d = action
#        self.viewactions.append({'prepmethod': dummy,'text': '3D View','kwargs': {'icon': icons['printapede'],'triggered': lambda: self.showhide2(self.view_3d_dock,self.act_view_3d)}})
#
#        def dummy(action):
#            action.setCheckable(True)
#            action.setChecked(True)
#            self.act_view_ops = action
#        self.viewactions.append({'prepmethod': dummy,'text': 'Operations','kwargs': {'icon': icons['operations'],'triggered': lambda: self.showhide2(self.operationdock,self.act_view_ops)}})
#
#        def dummy(action):
#            action.setCheckable(True)
#            action.setChecked(True)
#            self.act_view_layers = action
#        self.viewactions.append({'prepmethod': dummy,'text': 'Layers','kwargs': {'icon': icons['layers'],'triggered': lambda: self.showhide2(self.layerlistwidgetdock,self.act_view_layers)}})
#
#        def dummy(action):
#            action.setCheckable(True)
#            action.setChecked(False)
#            self.act_view_errors = action
#        self.viewactions.append({'prepmethod': dummy, 'text': 'Error Log', 'kwargs': {'triggered': lambda: self.showhide2(self.error_log, self.act_view_errors)}})
#
#        self.viewactions.append({'text': 'Zoom Fit','kwargs': {'triggered': self.view_2d.zoomToFit,'shortcut': 'Ctrl+F'}})
#        self.viewactions.append({'text': 'Screenshot','kwargs': {'triggered': self.scene.screenShot,'shortcut': 'Ctrl+R'}})
#        self.viewactions.append({'text': '3D Screenshot', 'kwargs': {'triggered': self.screenshot_3d}})
#
#        self.tools1 = []
#        self.tools1.append({'text': 'Cleanup','kwargs': {'icon': icons['cleanup'],'triggered': lambda: self.newoperation(popupcad.manufacturing.cleanup2.Cleanup2)}})
#        self.tools1.append({'text': 'New Cleanup','kwargs': {'icon': icons['cleanup'],'triggered': lambda: self.newoperation(popupcad.manufacturing.cleanup3.Cleanup3)}})
#        self.tools1.append({'text': 'Simplify','kwargs': {'icon': icons['simplify'],'triggered': lambda: self.newoperation(popupcad.manufacturing.simplify2.Simplify2)}})
#        self.tools1.append({'text': 'JointOp','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.joint_operation3.JointOperation3)}})
#        self.tools1.append({'text': 'HoleOp','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.hole_operation.HoleOperation)}})
#        self.tools1.append({'text': 'Freeze', 'kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.freeze.Freeze)}})
#        self.tools1.append({'text': 'Cross-Section','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.cross_section.CrossSection)}})
#        self.tools1.append({'text': 'SubOp','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.sub_operation2.SubOperation2)}})
#        self.tools1.append({'text': 'Code Exec','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.code_exec_op.CodeExecOperation)}})
#
#        transform = []
#        transform.append({'text': 'Internal Transform','kwargs': {'icon': icons['placeop'],'shortcut': 'Ctrl+Shift+P','triggered': lambda: self.newoperation(popupcad.manufacturing.transform_internal.TransformInternal)}})
#        transform.append({'text': 'External Transform','kwargs': {'icon': icons['placeop'],'shortcut': 'Ctrl+Shift+P','triggered': lambda: self.newoperation(popupcad.manufacturing.transform_external.TransformExternal)}})
##        transform.append({'text': '&PlaceOp','kwargs': {'icon': icons['placeop'],'shortcut': 'Ctrl+Shift+P','triggered': lambda: self.newoperation(popupcad.manufacturing.placeop8.PlaceOperation8)}})
##        transform.append({'text': 'L&ocateOp','kwargs': {'icon': icons['locate'],'shortcut': 'Ctrl+Shift+O','triggered': lambda: self.newoperation(popupcad.manufacturing.locateoperation3.LocateOperation3)}})
#        transform.append({'text': 'Shift/Flip','kwargs': {'icon': icons['shiftflip'],'triggered': lambda: self.newoperation(popupcad.manufacturing.shiftflip3.ShiftFlip3)}})
##        transform.append({'text': 'Transform','kwargs': {'triggered': lambda: self.newoperation(popupcad.manufacturing.transform.TransformOperation)}})
#
#        operationactions = []
#        operationactions.append({'text': '&SketchOp','kwargs': {'icon': icons['polygons'],'shortcut': 'Ctrl+Shift+S','triggered': lambda: self.newoperation(popupcad.manufacturing.simplesketchoperation.SimpleSketchOp)}})
#        operationactions.append({'text': '&LaminateOp','kwargs': {'icon': icons['metaop'],'shortcut': 'Ctrl+Shift+M','triggered': lambda: self.newoperation(popupcad.manufacturing.laminateoperation2.LaminateOperation2)}})
#        operationactions.append({'text': '&Dilate/Erode','kwargs': {'icon': icons['bufferop'],'shortcut': 'Ctrl+Shift+B','triggered': lambda: self.newoperation(popupcad.manufacturing.bufferop3.BufferOperation3)}})
#        operationactions.append({'text': 'Transform', 'submenu': transform,'kwargs':{'icon': icons['placeop']}})
#        operationactions.append({'text': '&LayerOp','kwargs': {'icon': icons['layerop'],'shortcut': 'Ctrl+Shift+L','triggered': lambda: self.newoperation(popupcad.manufacturing.layerop2.LayerOp2)}})
#        operationactions.append({'text': 'More...', 'submenu': self.tools1, 'kwargs': {}})
#
#        self.menu_file = self.addMenu(self.fileactions, name='File')
#        self.menu_project = self.addMenu(self.projectactions, name='Project')
#        self.menu_view = self.addMenu(self.viewactions, name='View')
#        self.toolbar_operations, self.menu_operations = self.addToolbarMenu(operationactions, name='Operations')
#
##        menu_bar = qg.QMenuBar()
##        menu_bar.addMenu(menu_file)
##        self.setMenuBar(menu_bar)
#        
#        self.showhide2(self.view_3d_dock, self.act_view_3d)
#        self.showhide2(self.operationdock, self.act_view_ops)
#        self.showhide2(self.layerlistwidgetdock, self.act_view_layers)
#        self.showhide2(self.error_log, self.act_view_errors)

    def operation_network(self):
        import popupcad.widgets.operationnetwork
        widget = popupcad.widgets.operationnetwork.action_method(self)
        hierarchy_dock = qg.QDockWidget()
        hierarchy_dock.setWidget(widget)
        hierarchy_dock.setAllowedAreas(qc.Qt.AllDockWidgetAreas)
        hierarchy_dock.setWindowTitle('Hierarchy')
        self.addDockWidget(qc.Qt.RightDockWidgetArea, hierarchy_dock)

#        widget.show()

    @property
    def design(self):
        return self._design

    @design.setter
    def design(self,design):
        self._design = design
    
    @design.deleter
    def design(self):
        del self._design
    
    def get_design(self):
        return self.design
    
    def newoperation(self, operationclass):
        operationclass.new(self,self.design,self.operationeditor.currentRow(),self.operationadded)
    
    def editoperation(self, operation):
        operation.edit(self, self.design, self.operationedited)

    def regen_id(self):
        self.design.regen_id()
    
    def newoperationslot(self, operation):
        self.design.append_operation(operation)
        if self.act_autoreprocesstoggle.isChecked():
            self.reprocessoperations([operation])
    
    def editedoperationslot(self, operation):
        if self.act_autoreprocesstoggle.isChecked():
            self.reprocessoperations([operation])
    
    def reprocessoperations_outer(self,operations = None):
        self.reprocessoperations(operations)
        
    def reprocessoperations(self, operations=None):
        try:
            self.design.reprocessoperations(operations)
            self.operationeditor.refresh()
            self.showcurrentoutput()
            self.view_2d.zoomToFit()
        except:
            raise
        finally:
            self.operationeditor.refresh()

    def newfile(self):
        from popupcad.filetypes.layerdef import LayerDef
        import popupcad.filetypes.material2 as materials
#        from popupcad.materials.materials import Carbon_0_90_0, Pyralux, Kapton
        design = Design.new()
        design.define_layers(LayerDef(*materials.default_sublaminate))
        self.load_design(design)
        self.view_2d.zoomToFit()

    def open(self, filename=None):
        if filename is None:
            design = Design.open(self)
        else:
            design = Design.load_yaml(filename)
        if not design is None:
            self.load_design(design)
            if self.act_autoreprocesstoggle.isChecked():
                self.reprocessoperations()
            self.view_2d.zoomToFit()

    def save(self):
        value = self.design.save(self)
        self.update_window_title()
        return value
    
    def saveAs(self, parent=None):
        value = self.design.saveAs(self)
        self.update_window_title()
        return value
    
    def load_design(self, design):
        self.design = design
        self.operationeditor.blockSignals(True)
        self.layerlistwidget.blockSignals(True)
        self.scene.deleteall()
        self.clear3dgeometry()

        self.operationeditor.set_tree_generator(self.design.build_tree)
        self.operationeditor.set_get_design(self.get_design)
        self.operationeditor.linklist(self.design.operations)

        self.updatelayerlist()
        self.layerlistwidget.selectAll()
        self.operationeditor.blockSignals(False)
        self.layerlistwidget.blockSignals(False)
        self.update_window_title()
    
    def editlayers(self):
        available_materials = popupcad.filetypes.material2.default_materials+popupcad.user_materials
        window = popupcad.widgets.materialselection.MaterialSelection(
            self.design.return_layer_definition().layers,
            available_materials,
            self)
        result = window.exec_()
        if result == window.Accepted:
            self.design.define_layers(window.layerdef)
        self.updatelayerlist()
        self.layerlistwidget.selectAll()
    
    def editlaminate(self):
        from dev_tools.propertyeditor import PropertyEditor
        dialog = self.builddialog(PropertyEditor(self.design.return_layer_definition().layers))
        dialog.exec_()
        del self.design.return_layer_definition().z_values
    
    def sketchlist(self):
        from popupcad.widgets.listmanager import AdvancedSketchListManager
        widget = AdvancedSketchListManager(self.design)
        dialog = self.builddialog(widget)
        dialog.setWindowTitle('Sketches')
        dialog.exec_()

    def subdesigns(self):
        from popupcad.widgets.listmanager import AdvancedDesignListManager
        widget = AdvancedDesignListManager(self.design)
        dialog = self.builddialog(widget)
        dialog.setWindowTitle('Sub-Designs')
        dialog.exec_()

    def updatelayerlist(self):
        self.layerlistwidget.linklist(
            self.design.return_layer_definition().layers)

    def showcurrentoutput(self):
        if len(self.design.operations)>0:
            selected_indeces = self.operationeditor.currentIndeces2()
            if len(selected_indeces) > 0:
                ii, jj = selected_indeces[0]
            else:
                ii, jj = -1, 0
                self.operationeditor.selectIndeces([(ii, jj)])
            self.showcurrentoutput_inner(ii, jj)

    def showcurrentoutput_inner(self, ii, jj):
        self.scene.deleteall()
        self.view_3d.view.clear()
        try:
            operationoutput = self.design.operations[ii].output[jj]
        except IndexError:
            raise
        except AttributeError:
            raise NoOutput()
        selectedlayers = [item for item in self.design.return_layer_definition().layers if item in self.layerlistwidget.selectedData()]
        self.show2dgeometry3(operationoutput, selectedlayers)
        self.show3dgeometry3(operationoutput, selectedlayers)
    
    def show2dgeometry3(self, operationoutput, selectedlayers,):
        display_geometry_2d = operationoutput.display_geometry_2d()
        self.scene.deleteall()
        for layer in selectedlayers[::1]:
            for geom in display_geometry_2d[layer]:
                self.scene.addItem(geom)
                geom.setselectable(True)
    
    def show3dgeometry3(self, operationoutput, selectedlayers):
        if self.act_view_3d.isChecked():
            layerdef = self.design.return_layer_definition()
            triangles = operationoutput.triangles_by_layer
            self.view_3d.view.update_object(layerdef,triangles,selectedlayers)
        else:
            self.clear3dgeometry()

    def clear3dgeometry(self):
        tris = dict([(layer, []) for layer in self.design.return_layer_definition().layers])
        layerdef = self.design.return_layer_definition()
        self.view_3d.view.update_object(layerdef,tris,[])
    
    def exportLayerSVG(self):
        from popupcad.graphics2d.svg_support import OutputSelection

        win = OutputSelection()
        accepted = win.exec_()
        if not accepted:
            return

        selected_indeces = self.operationeditor.currentIndeces2()
        if len(selected_indeces) > 0:
            ii, jj = selected_indeces[0]
        else:
            ii, jj = -1, 0
            self.operationeditor.selectIndeces([(ii, jj)])

        generic_laminate = self.design.operations[ii].output[jj].generic_laminate()

        for layernum, layer in enumerate(self.design.return_layer_definition().layers[::1]):
            basename = self.design.get_basename() + '_' + str(self.design.operations[ii]) + '_layer{0:02d}.svg'.format(layernum + 1)
            scene = popupcad.graphics2d.graphicsscene.GraphicsScene()
            geoms = [item.outputstatic(brush_color=(1,1,1,0)) for item in generic_laminate.geoms[layer]]
            [scene.addItem(geom) for geom in geoms]
            scene.renderprocess(basename, *win.acceptdata())

    def closeEvent(self, event):
        if self.checkSafe():
            self.error_log.close()
            event.accept()
        else:
            event.ignore()

    def checkSafe(self):
        temp = qg.QMessageBox.warning(
            self,
            "Modified Document",
            'This file has been modified.\nDo you want to save your'
            'changes?',
            qg.QMessageBox.Save | qg.QMessageBox.Discard | qg.QMessageBox.Cancel)
        if temp == qg.QMessageBox.Save:
            return self.save()
        elif temp == qg.QMessageBox.Cancel:
            return False
        return True
    
#    def preferences(self):
#        import dev_tools.propertyeditor
#        pe = dev_tools.propertyeditor.PropertyEditor(popupcad.local_settings)
#        pe.show()

    def replace(self):
        d = qg.QDialog()
        operationlist = popupcad.widgets.dragndroptree.DraggableTreeWidget()
        operationlist.linklist(self.design.operations)
        button1 = qg.QPushButton('Ok')
        button2 = qg.QPushButton('Cancel')
        layout2 = qg.QHBoxLayout()
        layout2.addWidget(button1)
        layout2.addWidget(button2)
        layout3 = qg.QVBoxLayout()
        layout3.addWidget(operationlist)
        layout3.addLayout(layout2)
        d.setLayout(layout3)
        button1.clicked.connect(d.accept)
        button2.clicked.connect(d.reject)
        result = d.exec_()
        if result:
            self.design.replace_op_refs(
                self.operationeditor.currentRefs()[0],
                operationlist.currentRefs()[0])
        self.reprocessoperations()
    
    def insert_and_replace(self):
        from popupcad.manufacturing.laminateoperation2 import LaminateOperation2
        operation_ref, output_index = self.operationeditor.currentRefs()[0]
        operation_index = self.design.operation_index(operation_ref)
        newop = LaminateOperation2({'unary': [], 'binary': []}, 'union')
        self.design.insert_operation(operation_index + 1, newop)
        self.design.replace_op_refs(
            (operation_ref, output_index), (newop.id, 0))
        newop.operation_links['unary'].append((operation_ref, output_index))
        self.reprocessoperations()

    def upgrade(self):
        try:
            self.load_design(self.design.upgrade())
        except popupcad.filetypes.design.UpgradeError as ex:
            print(ex)
            raise
        if self.act_autoreprocesstoggle.isChecked():
            self.reprocessoperations()
        self.view_2d.zoomToFit()
    
    def download_installer(self):
        qg.QDesktopServices.openUrl(popupcad.update_url)
    
    def save_joint_def(self):
        self.design.save_joint_def()
    
    def screenshot_3d(self):
        time = popupcad.basic_functions.return_formatted_time()
        filename = os.path.normpath(
            os.path.join(
                popupcad.exportdir,
                '3D_screenshot_' +
                time +
                '.png'))
        self.view_3d.view.grabFrameBuffer().save(filename)
    
    def export_laminate(self):
        ii, jj = self.operationeditor.currentIndeces2()[0]
        output = self.design.operations[ii].output[jj]
        generic = output.csg.to_generic_laminate()
        generic.saveAs()
    
    def gen_icons(self):
        self.design.raster()
    
    def build_documentation(self):
        self.design.build_documentation()

    def export_dxf(self):
        ii, jj = self.operationeditor.currentIndeces2()[0]
        output = self.design.operations[ii].output[jj]
        generic = output.generic_laminate()
        basename = self.design.get_basename() + '_'+str(self.design.operations[ii])
        generic.save_dxf(basename)
    
    def export_dxf_layers(self):
        ii, jj = self.operationeditor.currentIndeces2()[0]
        output = self.design.operations[ii].output[jj]
        generic = output.generic_laminate()
        basename = self.design.get_basename() + '_'+str(self.design.operations[ii])
        generic.save_dxf(basename,True)

    def export_dae(self):
        ii, jj = self.operationeditor.currentIndeces2()[0]
        output = self.design.operations[ii].output[jj]
        output.generic_laminate().toDAE()

    def export_stl(self):
        ii, jj = self.operationeditor.currentIndeces2()[0]
        output = self.design.operations[ii].output[jj]
        output.generic_laminate().toSTL()

    def show_license(self):
        import sys

        if hasattr(sys,'frozen'):
            path = popupcad.localpath
        else:
            path = os.path.normpath(os.path.join(popupcad.localpath,'../'))

        path = os.path.normpath(os.path.join(path,'LICENSE'))
        with open(path) as f:
            license_text = f.readlines()

        w = qg.QDialog()
        le = qg.QTextEdit()
        le.setText(''.join(license_text))
        le.setReadOnly(True)
        le.show()
        layout = qg.QVBoxLayout()
        layout.addWidget(le)        
        w.setLayout(layout)
        f = lambda: qc.QSize(600,400)
        w.sizeHint = f
        w.exec_()
    
    def update_window_title(self):
        basename = self.design.get_basename()
        self.setWindowTitle('Editor'+' - '+basename)


if __name__ == "__main__":
    app = qg.QApplication(sys.argv)
    icons = popupcad.guis.icons.build()
    app.setWindowIcon(icons['printapede'])
    mw = Editor()
    mw.show()
    mw.raise_()
    sys.exit(app.exec_())
