import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';


import { AppComponent } from './app.component';
import {RouterModule, Routes} from "@angular/router";
import { DashboardComponent } from './dashboard/dashboard.component';

import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { HttpClientModule } from '@angular/common/http';
import { NgApexchartsModule } from 'ng-apexcharts';
import { ButtonModule, ChartModule, ConfirmationService, DropdownModule, EditorModule, FieldsetModule, InputMaskModule, InputTextareaModule, InputTextModule, ListboxModule, MenuModule, PanelModule, RadioButtonModule, TooltipModule } from 'primeng/primeng';

const appRoutes: Routes = [
  { path: "", redirectTo: "/dashboard", pathMatch: "full" },
  { path: "dashboard", component: DashboardComponent },
];

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    HttpModule,
    HttpClientModule,
    RouterModule.forRoot(appRoutes, { relativeLinkResolution: 'legacy' }),
    BrowserAnimationsModule,
    MenuModule,
    PanelModule,
    ChartModule,
    InputTextModule,
    ButtonModule,
    InputMaskModule,
    InputTextareaModule,
    EditorModule,
    RadioButtonModule,
    FieldsetModule,
    DropdownModule,
    ListboxModule,
    NgApexchartsModule,
    TooltipModule
  ],
  providers: [ ConfirmationService ],
  bootstrap: [AppComponent]
})
export class AppModule { }
